use serde_json::Value;

/// Maximum allowed length (in bytes) for a single message line.
pub const MAX_MESSAGE_LINE_LENGTH: usize = 1048576;

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
    if line.starts_with("PIME_MSG|") {
        let parts: Vec<&str> = line.splitn(3, '|').collect();
        if parts.len() == 3 {
            let client_id = parts[1].to_string();
            let payload = parts[2].to_string();
            return Some((client_id, payload));
        }
    }
    None
}

/// Formats a message to be sent to a backend process.
///
/// Format: <client_id>|<payload>
pub fn format_backend_input(client_id: &str, message: &str) -> String {
    format!("{}|{}", client_id, message)
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
}
