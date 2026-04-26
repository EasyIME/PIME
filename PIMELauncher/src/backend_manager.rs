use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::process::Command;
use tokio::sync::{mpsc, Mutex};
use tracing::{debug, error, info, warn};

use crate::backend_registry::{BackendConfig, BackendRegistry};
use crate::protocol;
use futures::{SinkExt, StreamExt};
use tokio_util::codec::{FramedRead, FramedWrite, LinesCodec};

/// Manages the lifecycle of backend processes and routes messages between clients and backends.
#[derive(Clone)]
pub struct BackendManager {
    state: Arc<Mutex<BackendManagerState>>,
    registry: Arc<BackendRegistry>,
}

struct BackendManagerState {
    backends: HashMap<String, BackendProcess>,
    clients: HashMap<String, mpsc::Sender<String>>,
}

struct BackendProcess {
    stdin_tx: mpsc::Sender<String>,
}

impl BackendManager {
    /// Creates a new BackendManager with the given registry and root directory.
    pub fn new(registry: BackendRegistry) -> Self {
        Self {
            state: Arc::new(Mutex::new(BackendManagerState {
                backends: HashMap::new(),
                clients: HashMap::new(),
            })),
            registry: Arc::new(registry),
        }
    }

    /// Resolves a Text Service GUID to a backend name using the registry.
    /// Also supports direct backend names for legacy compatibility.
    pub fn resolve_backend(&self, identifier: &str) -> Option<String> {
        if let Some(name) = self.registry.resolve_guid(identifier) {
            return Some(name.clone());
        }
        // If not a GUID, check if it's a valid backend name directly
        if self.registry.get_backend(identifier).is_some() {
            return Some(identifier.to_string());
        }
        None
    }

    /// Registers a client with its response channel.
    pub async fn register_client(&self, client_id: String) -> mpsc::Receiver<String> {
        let mut state = self.state.lock().await;
        let (tx, rx) = tokio::sync::mpsc::channel::<String>(1024);
        state.clients.insert(client_id, tx);
        rx
    }

    /// Unregisters a client and notifies the backend of the disconnect.
    pub async fn unregister_client(&self, client_id: &str, backend_name: &str) {
        // Notify the backend that the client is closing
        self.send_to_backend(backend_name, client_id, r#"{"method":"close"}"#)
            .await;

        let mut state = self.state.lock().await;
        state.clients.remove(client_id);
    }

    /// Retrieves a channel to send messages directly to the backend.
    pub async fn get_backend_input(&self, backend_name: &str) -> Option<mpsc::Sender<String>> {
        let mut state = self.state.lock().await;
        if !state.backends.contains_key(backend_name) {
            // Dynamically look up the backend configuration
            if let Some(config) = self.registry.get_backend(backend_name) {
                let backend = self.spawn_backend_process(config).await;
                state.backends.insert(backend_name.to_string(), backend);
            } else {
                error!("Unknown backend requested: {}", backend_name);
                return None;
            }
        }
        state.backends.get(backend_name).map(|b| b.stdin_tx.clone())
    }

    /// Sends a message to a specific backend, spawning it if necessary.
    ///
    /// The message is prefixed with the client ID to allow the backend to identify the sender.
    pub async fn send_to_backend(&self, backend_name: &str, client_id: &str, message: &str) {
        if let Some(backend_stdin) = self.get_backend_input(backend_name).await {
            let formatted_msg = protocol::format_backend_input(client_id, message);
            debug!(
                "Sending message to backend {}: client={}, size={}",
                backend_name,
                client_id,
                formatted_msg.len()
            );
            if let Err(e) = backend_stdin.send(formatted_msg).await {
                error!(
                    "Failed to send to internal channel for backend {}: {}",
                    backend_name, e
                );
                // The backend task seems to be dead.
                let mut state = self.state.lock().await;
                state.backends.remove(backend_name);
            }
        }
    }

    /// Spawns a backend process and maintains its lifetime in a background task.
    async fn spawn_backend_process(&self, config: &BackendConfig) -> BackendProcess {
        let backend_name = config.name.clone();
        let (stdin_tx, mut stdin_rx) = mpsc::channel::<String>(1024);
        let backend_name_clone = backend_name.to_string();
        let manager_clone = self.clone();
        let config_clone = config.clone();

        tokio::spawn(async move {
            loop {
                let mut child_process = match Self::create_backend_process(
                    &config_clone,
                    &manager_clone.registry.top_dir,
                ) {
                    Ok(c) => c,
                    Err(e) => {
                        error!("Failed to spawn backend {}: {}", backend_name_clone, e);
                        tokio::time::sleep(Duration::from_secs(5)).await;
                        continue;
                    }
                };

                let stdin = child_process.stdin.take().unwrap();
                let stdout = child_process.stdout.take().unwrap();
                let stderr = child_process.stderr.take().unwrap();

                let last_output_time = Arc::new(AtomicU64::new(Self::current_ms()));
                let last_output_time_clone = last_output_time.clone();

                let manager_for_reader = manager_clone.clone();
                let stdout_task = tokio::spawn(async move {
                    manager_for_reader
                        .forward_outputs_to_client(stdout, last_output_time_clone)
                        .await;
                });

                let backend_name_for_stderr = backend_name_clone.clone();
                let stderr_task = tokio::spawn(async move {
                    Self::log_backend_stderr(stderr, backend_name_for_stderr).await;
                });

                Self::forward_inputs_to_backend(
                    &mut stdin_rx,       // Inputs received from client connections.
                    stdin,               // Backend stdin.
                    &mut child_process,  // Backend process.
                    &backend_name_clone, // Backend name.
                    last_output_time,    // Output tracker.
                )
                .await;

                stdout_task.abort();
                stderr_task.abort();
                warn!("Restarting backend {}", backend_name_clone);
                tokio::time::sleep(Duration::from_secs(1)).await;
            }
        });

        BackendProcess { stdin_tx }
    }

    /// Background task that reads backend stderr and logs it.
    async fn log_backend_stderr(stderr: tokio::process::ChildStderr, backend_name: String) {
        let mut stderr_reader = FramedRead::new(stderr, LinesCodec::new_with_max_length(1048576));
        while let Some(result) = stderr_reader.next().await {
            match result {
                Ok(line) => error!("[{} stderr] {}", backend_name, line),
                Err(e) => {
                    error!("[{} stderr] Error reading stream: {}", backend_name, e);
                    break;
                }
            }
        }
        info!("Backend {} stderr stream closed.", backend_name);
    }

    /// Helper to create the actual OS process for a backend.
    fn create_backend_process(
        config: &BackendConfig,
        top_dir: &std::path::Path,
    ) -> std::io::Result<tokio::process::Child> {
        let executable_path = top_dir.join(&config.command);
        let working_dir = top_dir.join(&config.working_dir);
        let params = config.params.clone();

        info!(
            "Spawning backend: {} (exe: {:?}, cwd: {:?}, params: {})",
            config.name, executable_path, working_dir, params
        );

        let args_vec: Vec<&str> = params.split_whitespace().collect();
        debug!(
            "Execution Details: {:?} with args {:?}",
            executable_path, args_vec
        );

        const CREATE_NO_WINDOW: u32 = 0x08000000;

        let mut child_cmd = Command::new(&executable_path);
        child_cmd
            .args(&args_vec)
            .current_dir(&working_dir)
            .creation_flags(CREATE_NO_WINDOW)
            .env("PYTHONIOENCODING", "utf-8:ignore")
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .kill_on_drop(true);

        child_cmd.spawn()
    }

    /// Background task that reads backend output and routes it to clients.
    async fn forward_outputs_to_client(
        self,
        stdout: tokio::process::ChildStdout,
        last_output_time: Arc<AtomicU64>,
    ) {
        // TODO: Need to detect if the backend process hangs and is not responsive.
        // When a backend process hangs, reading from its stdout may blocks forever.
        let mut stdout_reader = FramedRead::new(stdout, LinesCodec::new_with_max_length(1048576));
        while let Some(result) = stdout_reader.next().await {
            last_output_time.store(Self::current_ms(), Ordering::SeqCst);
            let line = match result {
                Ok(l) => l,
                Err(e) => {
                    error!("Error reading from backend stdout: {}", e);
                    break;
                }
            };

            debug!("Backend Output Raw: {:?}", line);
            let Some((client_id, payload)) = protocol::parse_backend_output(&line) else {
                continue;
            };

            debug!("Routing to client {}: {:?}", client_id, payload);

            let tx = {
                let state = self.state.lock().await;
                state.clients.get(&client_id).cloned()
            };

            if let Some(tx) = tx {
                // Use a timeout to avoid blocking the backend output indefinitely if a client is slow.
                // We give the client 500ms to clear some space in their buffer.
                // Note: We don't add a newline here anymore; the client writer will handle it.
                if let Err(_) =
                    tokio::time::timeout(Duration::from_millis(500), tx.send(payload)).await
                {
                    warn!("Client {} buffer full for 500ms. Force disconnecting to prevent backend stall.", client_id);
                    let mut state = self.state.lock().await;
                    state.clients.remove(&client_id);
                }
            } else {
                warn!(
                    "Received message for unknown client {}: {}",
                    client_id, payload
                );
            }
        }
        info!("Backend output routing stopped for a backend instance.");
    }

    /// Forwards messages from the internal channel to the backend's stdin.
    async fn forward_inputs_to_backend(
        stdin_rx: &mut mpsc::Receiver<String>,
        stdin: tokio::process::ChildStdin,
        child_process: &mut tokio::process::Child,
        backend_name: &str,
        last_output_time: Arc<AtomicU64>,
    ) {
        let mut stdin_writer = FramedWrite::new(stdin, LinesCodec::new_with_max_length(1048576));
        let mut last_request_time: Option<u64> = None;

        let mut watchdog_interval = tokio::time::interval(Duration::from_secs(1));

        loop {
            tokio::select! {
                msg = stdin_rx.recv() => {
                    let Some(data) = msg else { 
                        info!("Backend {} stdin channel closed. Exiting input loop.", backend_name);
                        break; 
                    };
                    let now = Self::current_ms();
                    last_request_time = Some(now);
                    info!("Backend {} received request from channel. Data len: {}. req_t={}", backend_name, data.len(), now);
                    
                    // LinesCodec expects data without the newline, it will add it for us.
                    let write_res = tokio::time::timeout(Duration::from_secs(5), stdin_writer.send(data)).await;
                    if let Err(_) = write_res {
                        error!("Timeout writing to backend {}. Forcing restart.", backend_name);
                        let _ = child_process.kill().await;
                        break;
                    }
                    if let Err(e) = write_res.unwrap() {
                        error!("Failed to write to backend {}: {}", backend_name, e);
                        let _ = child_process.kill().await;
                        break;
                    }
                }
                _ = watchdog_interval.tick() => {
                    let now = Self::current_ms();
                    if let Some(req_t) = last_request_time {
                        let last_out = last_output_time.load(Ordering::SeqCst);
                        // Log tick status occasionally or at least for debugging
                        info!("Watchdog tick for {}: last_out={}, req_t={}, now={}, delta={}", 
                            backend_name, last_out, req_t, now, now as i64 - req_t as i64);
                        
                        // If no output has been received since the last request and it's been more than 15 seconds
                        if last_out < req_t && (now - req_t) > 15000 {
                            error!("Backend {} seems to be hung (no output for 15s after request). last_out={}, req_t={}, now={}. Forcing restart.", 
                                backend_name, last_out, req_t, now);
                            let _ = child_process.kill().await;
                            break;
                        }
                    }
                }
                status = child_process.wait() => {
                    warn!("Backend {} exited with status {:?}", backend_name, status);
                    break;
                }
            }
        }
    }

    fn current_ms() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::backend_registry::BackendRegistry;

    #[tokio::test]
    async fn test_client_registration() {
        let registry = BackendRegistry::new();
        let manager = BackendManager::new(registry);

        let _ = manager.register_client("client1".to_string()).await;

        {
            let state = manager.state.lock().await;
            assert!(state.clients.contains_key("client1"));
        }

        manager.unregister_client("client1", "dummy").await;
        {
            let state = manager.state.lock().await;
            assert!(!state.clients.contains_key("client1"));
        }
    }
}
