use crate::protocol;
use futures::{SinkExt, StreamExt};
use tokio::io::{AsyncRead, AsyncWrite};
use tokio_util::codec::{FramedRead, FramedWrite, LinesCodec};
use tracing::error;

/// Represents a fully authenticated and established client connection.
///
/// This struct holds all the necessary state to stream data back and forth
/// between the Windows named pipe client and the PIME backend process.
pub struct ClientSession<R, W> {
    /// The unique identifier assigned to this client connection (UUID).
    client_id: String,
    /// The stream reader for receiving data from the client's named pipe.
    pipe_reader: FramedRead<R, LinesCodec>,
    /// The stream writer for sending data to the client's named pipe.
    pipe_writer: FramedWrite<W, LinesCodec>,
    /// The channel used to send messages directly to the backend process's stdin.
    backend_input: tokio::sync::mpsc::Sender<String>,
    /// The channel used to receive messages from the backend process targeted at this client.
    backend_output: tokio::sync::mpsc::Receiver<String>,
}

impl<R, W> ClientSession<R, W>
where
    R: AsyncRead + Unpin + Send + 'static,
    W: AsyncWrite + Unpin + Send + 'static,
{
    pub fn new(
        client_id: String,
        pipe_reader: FramedRead<R, LinesCodec>,
        pipe_writer: FramedWrite<W, LinesCodec>,
        backend_input: tokio::sync::mpsc::Sender<String>,
        backend_output: tokio::sync::mpsc::Receiver<String>,
    ) -> Self {
        Self {
            client_id,
            pipe_reader,
            pipe_writer,
            backend_input,
            backend_output,
        }
    }

    pub fn id(&self) -> &str {
        &self.client_id
    }

    pub async fn run(&mut self) {
        loop {
            tokio::select! {
                res = self.pipe_reader.next() => {
                    if !self.process_client_input(res).await {
                        break;
                    }
                }
                res = self.backend_output.recv() => {
                    if !self.process_backend_output(res).await {
                        break;
                    }
                }
            }
        }
    }

    async fn process_client_input(
        &mut self,
        msg: Option<Result<String, tokio_util::codec::LinesCodecError>>,
    ) -> bool {
        match msg {
            Some(Ok(line)) => {
                if line.is_empty() {
                    return true;
                }
                let formatted_msg = protocol::format_backend_input(&self.client_id, &line);
                if let Err(e) = self.backend_input.send(formatted_msg).await {
                    error!("Failed to send to backend channel: {}", e);
                    return false;
                }
                true
            }
            Some(Err(e)) => {
                error!("Error reading from client {}: {}", self.client_id, e);
                false
            }
            None => false,
        }
    }

    async fn process_backend_output(&mut self, msg: Option<String>) -> bool {
        match msg {
            Some(msg) => {
                if let Err(e) = self.pipe_writer.send(msg).await {
                    error!("Failed to write to client {}: {}", self.client_id, e);
                    return false;
                }
                true
            }
            None => false,
        }
    }
}
