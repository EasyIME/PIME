use crate::acl::PipeSecurityAttributes;
use crate::backend_manager::BackendManager;
use crate::client_session::ClientSession;
use crate::protocol::{self};
use futures::StreamExt; // For next() on FramedRead
use tokio::io::{AsyncRead, AsyncWrite};
use tokio::net::windows::named_pipe::{PipeMode, ServerOptions};
use tokio_util::codec::{FramedRead, FramedWrite, LinesCodec};
use tracing::{error, info};
use uuid::Uuid;

#[derive(Clone)]
pub struct PipeServer {
    pipe_name: String,
    manager: BackendManager,
}

impl PipeServer {
    pub fn new(pipe_name: String, manager: BackendManager) -> Self {
        Self { pipe_name, manager }
    }

    /// Starts the named pipe server loop.
    ///
    /// This function creates the pipe instances, applies security attributes,
    /// and spawns a handler for each connected client.
    pub async fn run(&self) {
        let sa = PipeSecurityAttributes::new().expect("Failed to create PipeSecurityAttributes");
        let mut is_first_instance = true;

        loop {
            let mut options = ServerOptions::new();
            options.first_pipe_instance(is_first_instance);
            options.max_instances(254);
            options.pipe_mode(PipeMode::Byte);

            // Tokio 1.x allows creating with raw security attributes
            let server = match unsafe {
                options.create_with_security_attributes_raw(
                    &self.pipe_name,
                    &sa.sa as *const _ as *mut std::ffi::c_void,
                )
            } {
                Ok(server) => server,
                Err(e) => {
                    error!("Failed to create named pipe server: {}", e);
                    tokio::time::sleep(std::time::Duration::from_secs(1)).await;
                    continue;
                }
            };

            match server.connect().await {
                Ok(_) => {
                    info!(
                        "Client connection accepted on pipe instance (first_instance={}).",
                        is_first_instance
                    );
                    is_first_instance = false;
                    let manager = self.manager.clone();
                    tokio::spawn(async move {
                        let (reader, writer) = tokio::io::split(server);
                        Self::handle_client(manager, reader, writer).await;
                    });
                }
                Err(e) => {
                    error!("Failed to accept client connection: {}", e);
                    tokio::time::sleep(std::time::Duration::from_millis(100)).await;
                }
            }
        }
    }
    /// Generic implementation of the client handler to allow unit testing with mocked I/O.
    pub async fn handle_client<R, W>(manager: BackendManager, pipe_reader: R, pipe_writer: W)
    where
        R: AsyncRead + Unpin + Send + 'static,
        W: AsyncWrite + Unpin + Send + 'static,
    {
        let (mut client, backend_name) =
            match Self::accept_client(&manager, pipe_reader, pipe_writer).await {
                Ok(v) => v,
                Err(e) => {
                    error!("Failed to accept client: {}", e);
                    return;
                }
            };

        // Run the session
        client.run().await;

        // Phase 3: Cleanup on disconnect
        info!(
            "Client disconnected: id={}, backend={}",
            client.id(),
            backend_name
        );
        manager.unregister_client(client.id(), &backend_name).await;
    }

    /// Performs the handshake and initializes the client session.
    async fn accept_client<R, W>(
        manager: &BackendManager,
        pipe_reader: R,
        pipe_writer: W,
    ) -> Result<(ClientSession<R, W>, String), String>
    where
        R: AsyncRead + Unpin + Send + 'static,
        W: AsyncWrite + Unpin + Send + 'static,
    {
        let client_id = Uuid::new_v4().to_string();
        info!("Client connected: id={}", client_id);

        let mut line_reader = FramedRead::new(
            pipe_reader,
            LinesCodec::new_with_max_length(protocol::MAX_MESSAGE_LINE_LENGTH),
        );
        let line_writer = FramedWrite::new(
            pipe_writer,
            LinesCodec::new_with_max_length(protocol::MAX_MESSAGE_LINE_LENGTH),
        );

        let mut backend_name_opt = None;
        let mut handshake_line = None;

        // Phase 1: Wait for initial handshake
        while let Some(result) = line_reader.next().await {
            match result {
                Ok(line) => {
                    if line.is_empty() {
                        continue;
                    }

                    let input_method_guid = match protocol::parse_client_handshake(&line) {
                        Ok(g) => g,
                        Err(e) => {
                            return Err(format!("Handshake error from {}: {}", client_id, e));
                        }
                    };

                    let backend_name = match manager.resolve_backend(&input_method_guid) {
                        Some(n) => n,
                        None => {
                            let msg = format!(
                                "Backend not found for text service GUID: {} from {}",
                                input_method_guid, client_id
                            );
                            return Err(msg);
                        }
                    };

                    info!(
                        "Client {} handshake successful, mapped to backend: {}",
                        client_id, backend_name
                    );

                    backend_name_opt = Some(backend_name);
                    handshake_line = Some(line);
                    break;
                }
                Err(e) => {
                    return Err(format!("Error reading from client {}: {}", client_id, e));
                }
            }
        }

        let backend_name = match backend_name_opt {
            Some(name) => name,
            None => {
                return Err(format!(
                    "Client disconnected before handshake: id={}",
                    client_id
                ));
            }
        };

        let backend_writer = match manager.get_backend_input(&backend_name).await {
            Some(tx) => tx,
            None => {
                return Err(format!(
                    "Failed to get backend input channel for {}",
                    backend_name
                ));
            }
        };
        let backend_reader = manager.register_client(client_id.clone()).await;

        // Phase 2: Construct the fully authenticated session and run it
        let session = ClientSession::new(
            client_id.clone(),
            line_reader,
            line_writer,
            backend_writer.clone(),
            backend_reader,
        );

        // Forward the handshake itself to the backend directly via channel
        let formatted_handshake =
            protocol::format_backend_input(&client_id, handshake_line.as_deref().unwrap());
        if let Err(e) = backend_writer.send(formatted_handshake).await {
            return Err(format!("Failed to forward handshake to backend: {}", e));
        }

        Ok((session, backend_name))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::backend_registry::BackendRegistry;
    use tokio_test::io::Builder;

    #[tokio::test]
    async fn test_handle_client_fragmented() {
        // Setup manager with an empty registry and manually add test mapping
        let mut registry = BackendRegistry::new();
        registry.guid_to_backend.insert(
            crate::testing::GUID_TEST_ECHO.to_lowercase(),
            "echo".to_string(),
        );
        registry.backends.insert(
            "echo".to_string(),
            crate::backend_registry::BackendConfig {
                name: "echo".to_string(),
                command: "echo".to_string(),
                working_dir: "".to_string(),
                params: "".to_string(),
            },
        );
        let manager = BackendManager::new(registry);
        // Simulate a client sending data in multiple small chunks
        // 1. Handshake split: {"method": "init", "id": "{...}"}\n
        // 2. Data split: "Hello " + "World\nNext" + " Message\n"
        let handshake = format!(
            r#"{{"method": "init", "id": "{}"}}"#,
            crate::testing::GUID_TEST_ECHO
        );
        let h1 = &handshake[..handshake.len() / 2];
        let h2 = &handshake[handshake.len() / 2..];

        let reader = Builder::new()
            .read(h1.as_bytes())
            .read(format!("{}\n", h2).as_bytes())
            .read(b"Hello ")
            .read(b"World\nNext")
            .read(b" Message\n")
            .build();

        let writer = Builder::new().build();

        // Run the handler. It should process all lines and exit on EOF.
        let result = tokio::time::timeout(
            std::time::Duration::from_secs(2),
            PipeServer::handle_client(manager, reader, writer),
        )
        .await;

        assert!(result.is_ok(), "Handler hung or took too long");
    }

    #[tokio::test]
    async fn test_handle_client_utf8_split() {
        let mut registry = BackendRegistry::new();
        registry.guid_to_backend.insert(
            crate::testing::GUID_TEST_ECHO.to_lowercase(),
            "echo".to_string(),
        );
        registry.backends.insert(
            "echo".to_string(),
            crate::backend_registry::BackendConfig {
                name: "echo".to_string(),
                command: "echo".to_string(),
                working_dir: "".to_string(),
                params: "".to_string(),
            },
        );
        let manager = BackendManager::new(registry);
        // '中' is [0xE4, 0xB8, 0xAD]
        // We split it across two reads.
        let handshake = format!(
            r#"{{"method": "init", "id": "{}"}}"#,
            crate::testing::GUID_TEST_ECHO
        );
        let reader = Builder::new()
            .read(format!("{}\n", handshake).as_bytes())
            .read(b"\xE4")
            .read(b"\xB8\xAD\n")
            .build();

        let writer = Builder::new().build();

        let result = tokio::time::timeout(
            std::time::Duration::from_secs(2),
            PipeServer::handle_client(manager, reader, writer),
        )
        .await;

        assert!(
            result.is_ok(),
            "Handler failed to process split UTF-8 character"
        );
    }
}
