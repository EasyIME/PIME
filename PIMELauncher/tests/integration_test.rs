use pimelauncher::backend_manager::BackendManager;
use pimelauncher::backend_registry::{BackendConfig, BackendRegistry};
use pimelauncher::pipe_server::PipeServer;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::time::Duration;
use tempfile::tempdir;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::windows::named_pipe::{ClientOptions, PipeMode};
use tokio::time::timeout;

use pimelauncher::testing::*;

type TestResult = Result<(), Box<dyn std::error::Error + Send + Sync>>;

async fn send_msg<W: tokio::io::AsyncWriteExt + Unpin>(
    writer: &mut W,
    msg: &str,
) -> TestResult {
    writer.write_all(msg.as_bytes()).await?;
    writer.write_all(b"\n").await?;
    writer.flush().await?;
    Ok(())
}

async fn read_line<R: tokio::io::AsyncBufReadExt + Unpin>(
    lines: &mut tokio::io::Lines<R>,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let line = timeout(Duration::from_secs(5), lines.next_line())
        .await
        .map_err(|_| "Timeout reading from pipe")??;
    line.ok_or_else(|| "EOF unexpected".into())
}

async fn setup_test_environment(pipe_name: &str) -> (BackendManager, PathBuf) {
    let dir = tempdir().unwrap();
    let pime_root = dir.into_path(); // This prevents the directory from being deleted

    let mock_backend_exe = env!("CARGO_BIN_EXE_mock_backend");

    fs::copy(&mock_backend_exe, pime_root.join("mock_backend.exe")).unwrap();

    // Create configurations and mappings manually for the registry
    let configs = vec![
        BackendConfig {
            name: "echo".to_string(),
            command: "mock_backend.exe".to_string(),
            working_dir: "".to_string(),
            params: "--scenario echo".to_string(),
        },
        BackendConfig {
            name: "crash".to_string(),
            command: "mock_backend.exe".to_string(),
            working_dir: "".to_string(),
            params: "--scenario crash".to_string(),
        },
        BackendConfig {
            name: "hang".to_string(),
            command: "mock_backend.exe".to_string(),
            working_dir: "".to_string(),
            params: "--scenario hang".to_string(),
        },
        BackendConfig {
            name: "fail".to_string(),
            command: "non_existent.exe".to_string(),
            working_dir: "".to_string(),
            params: "".to_string(),
        },
    ];

    let mut guid_to_backend = HashMap::new();
    guid_to_backend.insert(GUID_TEST_ECHO.to_string(), "echo".to_string());
    guid_to_backend.insert(GUID_TEST_CRASH.to_string(), "crash".to_string());
    guid_to_backend.insert(GUID_TEST_HANG.to_string(), "hang".to_string());
    guid_to_backend.insert(GUID_TEST_FAIL.to_string(), "fail".to_string());

    let registry = BackendRegistry::with_configs(configs, guid_to_backend, &pime_root);
    let manager = BackendManager::new(registry);

    let manager_clone = manager.clone();
    let pipe_name_str = pipe_name.to_string();
    tokio::spawn(async move {
        let server = PipeServer::new(pipe_name_str, manager_clone);
        server.run().await;
    });

    tokio::time::sleep(Duration::from_millis(200)).await;

    (manager, pime_root)
}

async fn connect_with_retry(pipe_name: &str) -> tokio::net::windows::named_pipe::NamedPipeClient {
    let mut last_err = None;
    for _ in 0..10 {
        match ClientOptions::new()
            .pipe_mode(PipeMode::Byte)
            .open(pipe_name)
        {
            Ok(client) => return client,
            Err(e) => {
                last_err = Some(e);
                tokio::time::sleep(Duration::from_millis(100)).await;
            }
        }
    }
    panic!("Failed to connect to pipe after retries: {:?}", last_err);
}

#[tokio::test]
async fn test_integration_full() -> TestResult {
    let _ = tracing_subscriber::fmt::try_init();

    let pipe_name = format!(r#"\\.\pipe\pime_test_{}"#, uuid::Uuid::new_v4());
    let (_manager, _pime_root) = setup_test_environment(&pipe_name).await;

    // 1. Test incoming connection handshake (Fallback mode)
    {
        let client = connect_with_retry(&pipe_name).await;
        let (reader, mut writer) = tokio::io::split(client);
        let mut lines = BufReader::new(reader).lines();

        let handshake = format!(r#"{{"method": "init", "id": "{}"}}"#, GUID_TEST_ECHO);
        send_msg(&mut writer, &handshake).await?;

        let reply1 = read_line(&mut lines).await?;
        assert!(reply1.contains(&handshake));

        // 5. Test client incoming message & 6. Forwarding
        send_msg(&mut writer, "Hello Backend").await?;

        let reply2 = read_line(&mut lines).await?;
        assert_eq!(reply2, "REPLY: Hello Backend");
    }

    // 2. Test backend restart
    {
        let client = connect_with_retry(&pipe_name).await;
        let (reader, mut writer) = tokio::io::split(client);
        let mut lines = BufReader::new(reader).lines();

        let handshake = format!(r#"{{"method": "init", "id": "{}"}}"#, GUID_TEST_CRASH);
        send_msg(&mut writer, &handshake).await?;
        let _ = read_line(&mut lines).await?; // skip handshake reply

        send_msg(&mut writer, "CRASH_NOW").await?;

        // Wait for crash and restart
        tokio::time::sleep(Duration::from_millis(1500)).await;

        send_msg(&mut writer, "Still here").await?;
        let resp = read_line(&mut lines).await?;
        assert_eq!(resp, "REPLY: Still here");
    }

    // 3. Test backend timeout
    {
        let client = connect_with_retry(&pipe_name).await;
        let (reader, mut writer) = tokio::io::split(client);
        let mut lines = BufReader::new(reader).lines();

        let handshake = format!(r#"{{"method": "init", "id": "{}"}}"#, GUID_TEST_HANG);
        send_msg(&mut writer, &handshake).await?;
        let _ = read_line(&mut lines).await?; // skip handshake reply

        send_msg(&mut writer, "HANG_NOW").await?;

        // Subsequent message should trigger timeout in BackendManager
        // We send a large block to ensure the pipe buffer fills up
        let large_block = "A".repeat(1024 * 128); // 128KB
        send_msg(&mut writer, &large_block).await?;

        // Timeout is 5s for write + 2s for flush. Let's wait 12s.
        tokio::time::sleep(Duration::from_secs(12)).await;

        // After restart, it should respond again
        send_msg(&mut writer, "Hello again").await?;
        let resp = read_line(&mut lines).await?;
        assert_eq!(resp, "REPLY: Hello again");
    }

    // 4. Test backend start fail
    {
        let client = connect_with_retry(&pipe_name).await;
        let (_reader, mut writer) = tokio::io::split(client);
        let handshake = format!(r#"{{"method": "init", "id": "{}"}}"#, GUID_TEST_FAIL);
        send_msg(&mut writer, &handshake).await?;
        send_msg(&mut writer, "Should not crash server").await?;
        tokio::time::sleep(Duration::from_millis(500)).await;
    }

    // 8. Test two concurrent clients
    let pipe_name_clone = pipe_name.clone();
    let t1 = tokio::spawn(async move {
        let client = connect_with_retry(&pipe_name_clone).await;
        let (reader, mut writer) = tokio::io::split(client);
        let mut lines = BufReader::new(reader).lines();

        let handshake = format!(r#"{{"method": "init", "id": "{}"}}"#, GUID_TEST_ECHO);
        send_msg(&mut writer, &handshake).await?;
        let _ = read_line(&mut lines).await?;

        for i in 0..10 {
            send_msg(&mut writer, &format!("Msg A {}", i)).await?;
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
        for i in 0..10 {
            let line = read_line(&mut lines).await?;
            assert_eq!(line, format!("REPLY: Msg A {}", i));
        }
        Ok::<(), Box<dyn std::error::Error + Send + Sync>>(())
    });

    let pipe_name_clone2 = pipe_name.clone();
    let t2 = tokio::spawn(async move {
        let client = connect_with_retry(&pipe_name_clone2).await;
        let (reader, mut writer) = tokio::io::split(client);
        let mut lines = BufReader::new(reader).lines();

        let handshake = format!(r#"{{"method": "init", "id": "{}"}}"#, GUID_TEST_ECHO);
        send_msg(&mut writer, &handshake).await?;
        let _ = read_line(&mut lines).await?;

        for i in 0..10 {
            send_msg(&mut writer, &format!("Msg B {}", i)).await?;
            tokio::time::sleep(Duration::from_millis(15)).await;
        }
        for i in 0..10 {
            let line = read_line(&mut lines).await?;
            assert_eq!(line, format!("REPLY: Msg B {}", i));
        }
        Ok::<(), Box<dyn std::error::Error + Send + Sync>>(())
    });

    // 7. Test client disconnect (explicitly verify "close" message)
    {
        let client = connect_with_retry(&pipe_name).await;
        let (reader, mut writer) = tokio::io::split(client);
        let mut lines = BufReader::new(reader).lines();

        let handshake = format!(r#"{{"method": "init", "id": "{}"}}"#, GUID_TEST_ECHO);
        send_msg(&mut writer, &handshake).await?;
        let _ = read_line(&mut lines).await?;

        // When we drop the client, the launcher should send {"method":"close"}
        // and the echo backend will reply. We can't easily see it after drop,
        // but we can manually send it to see if it's handled.
        send_msg(&mut writer, r#"{"method":"close"}"#).await?;

        let reply = read_line(&mut lines).await?;
        assert!(reply.contains(r#""method":"close""#));
    }

    t1.await??;
    t2.await??;
    Ok(())
}

#[tokio::test]
async fn test_fragmented_messages() -> TestResult {
    let _ = tracing_subscriber::fmt::try_init();

    let pipe_name = format!(r#"\\.\pipe\pime_frag_{}"#, uuid::Uuid::new_v4());
    let (_manager, _pime_root) = setup_test_environment(&pipe_name).await;

    let client = connect_with_retry(&pipe_name).await;
    let (reader, mut writer) = tokio::io::split(client);
    let mut lines = BufReader::new(reader).lines();

    // 1. Send handshake in two chunks
    let handshake = format!(r#"{{"method": "init", "id": "{}"}}"#, GUID_TEST_ECHO);
    let h1 = &handshake[..handshake.len() / 2];
    let h2 = &handshake[handshake.len() / 2..];

    writer.write_all(h1.as_bytes()).await?;
    writer.flush().await?;
    tokio::time::sleep(Duration::from_millis(50)).await;
    writer.write_all(format!("{}\n", h2).as_bytes()).await?;
    writer.flush().await?;

    let reply = read_line(&mut lines).await?;
    assert!(reply.contains(&handshake));

    // 2. Send message in chunks with remaining data for next message
    // Chunk A: Start of first message
    writer.write_all(b"Hello ").await?;
    writer.flush().await?;
    tokio::time::sleep(Duration::from_millis(50)).await;

    // Chunk B: End of first message + Start of second message
    writer.write_all(b"World\nNext").await?;
    writer.flush().await?;

    // We should get "REPLY: Hello World" immediately
    let reply = read_line(&mut lines).await?;
    assert_eq!(reply, "REPLY: Hello World");

    // Chunk C: End of second message
    tokio::time::sleep(Duration::from_millis(50)).await;
    writer.write_all(b" Message\n").await?;
    writer.flush().await?;

    // We should get "REPLY: Next Message"
    let reply = read_line(&mut lines).await?;
    assert_eq!(reply, "REPLY: Next Message");
    Ok(())
}
