use serde_json::Value;
use std::time::Duration;

/// Maximum allowed length (in bytes) for a single message line.
pub const MAX_MESSAGE_LINE_LENGTH: usize = 1048576;

/// Exact length for a client ID string (standard UUID v4: 36 characters).
pub const CLIENT_ID_LENGTH: usize = 36;

/// Timeout for backend output hang detection.
pub const HANG_TIMEOUT: Duration = Duration::from_secs(15);

/// Timeout for backend write operations.
pub const BACKEND_WRITE_TIMEOUT: Duration = Duration::from_secs(5);

/// Parses the first line received from a client to determine which backend to use.
///
/// Supports standard `{"method": "init", "id": "{GUID}"}`.
pub fn parse_client_handshake(first_line: &str) -> Result<String, String> {
    let json: Value = serde_json::from_str(first_line).map_err(|e| e.to_string())?;

    if let Some(method) = json["method"].as_str() {
        if method == "init" {
            if let Some(guid) = json["id"].as_str() {
                return Ok(guid.to_string());
            }
            return Err("Missing 'id' field in init message".to_string());
        }
        return Err(format!("Unknown method '{}' in initial message", method));
    }
    Err("Invalid initial message format: missing 'method' field".to_string())
}

/// Parses a line of output from a backend process.
///
/// Expects the format `PIME_MSG|<client_id>|<payload>`.
/// Returns `Some((client_id, payload))` if valid.
pub fn parse_backend_output(line: &str) -> Option<(String, String)> {
    let rest = line.strip_prefix("PIME_MSG|")?;
    let sep = rest.find('|')?;
    Some((rest[..sep].to_string(), rest[sep + 1..].to_string()))
}

/// Formats a message to be sent to a backend process.
///
/// Format: <client_id>|<payload>
pub fn format_backend_input(client_id: &str, message: &str) -> String {
    format!("{}|{}", client_id, message)
}

/// Validates and parses a message to be sent to a backend process.
///
/// Expects `<client_id>|<payload>`, where `client_id` is exactly CLIENT_ID_LENGTH characters.
/// Returns `Some((client_id, payload))`.
pub fn parse_backend_input(data: &str) -> Option<(&str, &str)> {
    let (client_id, payload) = data.split_once('|')?;
    if client_id.len() != CLIENT_ID_LENGTH {
        return None;
    }
    Some((client_id, payload))
}

/// Extracts the `seqNum` field from a pure JSON payload (no `client_id|` prefix).
pub fn extract_seq_num(json_str: &str) -> Option<i64> {
    // Fast path: skip parsing messages that cannot contain a seqNum.
    if !json_str.contains("\"seqNum\"") {
        return None;
    }
    serde_json::from_str::<Value>(json_str)
        .ok()?
        .get("seqNum")?
        .as_i64()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_client_handshake_init() {
        let json = format!(
            r#"{{"method": "init", "id": "{}"}}"#,
            crate::testing::GUID_TEST_ECHO
        );
        match parse_client_handshake(&json) {
            Ok(guid) => assert_eq!(guid, crate::testing::GUID_TEST_ECHO),
            _ => panic!("Expected Init handshake"),
        }
    }

    #[test]
    fn test_parse_client_handshake_invalid() {
        assert!(parse_client_handshake("not json").is_err());
        assert!(parse_client_handshake(r#"{"method": "unknown"}"#).is_err());
        assert!(parse_client_handshake(r#"{"method": "init"}"#).is_err()); // missing id
    }

    #[test]
    fn test_parse_backend_output_valid() {
        let line = "PIME_MSG|client123|{\"status\": \"ok\"}";
        let (client_id, payload) = parse_backend_output(line).unwrap();
        assert_eq!(client_id, "client123");
        assert_eq!(payload, "{\"status\": \"ok\"}");
    }

    #[test]
    fn test_parse_backend_output_invalid() {
        assert!(parse_backend_output("JUST_TEXT").is_none());
        assert!(parse_backend_output("PIME_MSG|incomplete").is_none());
    }

    #[test]
    fn test_format_backend_input() {
        let client_id = "client123";
        let message = "{\"method\": \"test\"}";
        let formatted = format_backend_input(client_id, message);
        assert_eq!(formatted, "client123|{\"method\": \"test\"}");
    }

    #[test]
    fn test_extract_seq_num_with_pipe_in_payload() {
        assert_eq!(
            extract_seq_num(r#"{"commitString":"a|b","seqNum":7}"#),
            Some(7)
        );
        assert_eq!(extract_seq_num(r#"{"success":true}"#), None);
    }

    #[test]
    fn test_parse_backend_input() {
        let uuid = "12345678-1234-1234-1234-123456789012";
        let valid = format!("{}|{{\"method\":\"test\"}}", uuid);
        assert_eq!(
            parse_backend_input(&valid),
            Some((uuid, "{\"method\":\"test\"}"))
        );

        let valid_close = format!("{}|{{\"method\":\"close\",\"seqNum\":2}}", uuid);
        assert_eq!(
            parse_backend_input(&valid_close),
            Some((uuid, "{\"method\":\"close\",\"seqNum\":2}"))
        );

        // Missing pipe delimiter
        assert_eq!(parse_backend_input("no_delimiter"), None);

        // Empty client_id
        assert_eq!(parse_backend_input("|{\"method\":\"test\"}"), None);

        // Client ID not matching CLIENT_ID_LENGTH (36 chars)
        assert_eq!(parse_backend_input("short_id|{\"method\":\"test\"}"), None);
        let oversized = format!("{}extra|{{\"method\":\"test\"}}", uuid);
        assert_eq!(parse_backend_input(&oversized), None);
    }
}
