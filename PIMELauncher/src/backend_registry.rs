use serde::Deserialize;
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use tracing::{error, info, warn};

/// Configuration for a specific backend.
#[derive(Debug, Clone, Deserialize)]
pub struct BackendConfig {
    /// The unique name of the backend (e.g., "chewing").
    pub name: String,
    /// The executable command or script name to run.
    pub command: String,
    /// The working directory for the backend process, relative to PIME root.
    #[serde(rename = "workingDir")]
    pub working_dir: String,
    /// Command-line parameters to pass to the backend.
    pub params: String,
}

/// A registry that holds backend configurations and maps GUIDs to backend names.
#[derive(Debug, Clone)]
pub struct BackendRegistry {
    /// Map of backend names to their configurations.
    pub backends: HashMap<String, BackendConfig>,
    /// Map of Text Service GUIDs (lowercase) to backend names.
    pub guid_to_backend: HashMap<String, String>, // lowercase guid -> backend_name
    /// The root directory of the PIME installation.
    pub top_dir: std::path::PathBuf,
}

impl BackendRegistry {
    /// Creates a new empty registry.
    pub fn new() -> Self {
        Self {
            backends: HashMap::new(),
            guid_to_backend: HashMap::new(),
            top_dir: std::path::PathBuf::new(),
        }
    }

    /// Factory method to create a registry with pre-parsed configurations and mappings.
    pub fn with_configs(
        configs: Vec<BackendConfig>,
        guid_to_backend: HashMap<String, String>,
        top_dir: &Path,
    ) -> Self {
        let mut registry = Self::new();
        registry.top_dir = top_dir.to_path_buf();
        for config in configs {
            registry.backends.insert(config.name.clone(), config);
        }
        for (guid, backend_name) in guid_to_backend {
            registry
                .guid_to_backend
                .insert(guid.to_lowercase(), backend_name);
        }
        registry
    }

    /// Loads the registry from the specified PIME root directory.
    ///
    /// Reads `backends.json` and scans each backend's `input_methods` directory for `ime.json` files.
    pub fn load(top_dir: &Path) -> Self {
        let backends_json_path = top_dir.join("backends.json");
        if !backends_json_path.exists() {
            warn!("backends.json not found at {:?}", backends_json_path);
            let mut registry = Self::new();
            registry.top_dir = top_dir.to_path_buf();
            return registry;
        }

        let content = match fs::read_to_string(&backends_json_path) {
            Ok(c) => c,
            Err(e) => {
                error!("Failed to read backends.json: {}", e);
                let mut registry = Self::new();
                registry.top_dir = top_dir.to_path_buf();
                return registry;
            }
        };

        let configs: Vec<BackendConfig> = match serde_json::from_str(&content) {
            Ok(c) => c,
            Err(e) => {
                error!("Failed to parse backends.json: {}", e);
                let mut registry = Self::new();
                registry.top_dir = top_dir.to_path_buf();
                return registry;
            }
        };

        let mut guid_to_backend = HashMap::new();
        for config in &configs {
            Self::load_guid_mappings_for_backend(&config.name, top_dir, &mut guid_to_backend);
        }

        Self::with_configs(configs, guid_to_backend, top_dir)
    }

    /// Scans the `input_methods` directory for a backend and updates the GUID mappings.
    fn load_guid_mappings_for_backend(
        backend_name: &str,
        top_dir: &Path,
        mappings: &mut HashMap<String, String>,
    ) {
        let im_dir = top_dir.join(backend_name).join("input_methods");

        let Ok(entries) = fs::read_dir(&im_dir) else {
            return;
        };

        for entry in entries.flatten() {
            if let Some(guid) = Self::extract_guid_from_entry(&entry) {
                mappings.insert(guid.to_lowercase(), backend_name.to_string());
                info!("Mapped GUID {} to backend {}", guid, backend_name);
            }
        }
    }

    /// Attempts to extract the "guid" field from an `ime.json` file in a directory entry.
    fn extract_guid_from_entry(entry: &fs::DirEntry) -> Option<String> {
        let path = entry.path();
        if !path.is_dir() {
            return None;
        }

        let ime_json_path = path.join("ime.json");
        let content = fs::read_to_string(ime_json_path).ok()?;
        let json: serde_json::Value = serde_json::from_str(&content).ok()?;

        json["guid"].as_str().map(|s| s.to_string())
    }

    /// Resolves a Text Service GUID to a backend name.
    pub fn resolve_guid(&self, guid: &str) -> Option<&String> {
        self.guid_to_backend.get(&guid.to_lowercase())
    }

    /// Gets the configuration for a named backend.
    pub fn get_backend(&self, name: &str) -> Option<&BackendConfig> {
        self.backends.get(name)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn test_registry_load() {
        let dir = tempdir().unwrap();
        let pime_root = dir.path();

        // Create backends.json
        let backends_json = r#"[
            {
                "name": "chewing",
                "command": "python.exe",
                "workingDir": "chewing",
                "params": "main.py"
            }
        ]"#;
        fs::write(pime_root.join("backends.json"), backends_json).unwrap();

        // Create input method mapping
        let chewing_dir = pime_root.join("chewing");
        let im_dir = chewing_dir.join("input_methods").join("chewing_method");
        fs::create_dir_all(&im_dir).unwrap();

        let ime_json = r#"{"guid": "{ABC-123}"}"#;
        fs::write(im_dir.join("ime.json"), ime_json).unwrap();

        let registry = BackendRegistry::load(pime_root);

        assert_eq!(registry.backends.len(), 1);
        assert!(registry.backends.contains_key("chewing"));

        // Test GUID resolution
        assert_eq!(
            registry.resolve_guid("{abc-123}"),
            Some(&"chewing".to_string())
        );
        assert_eq!(
            registry.resolve_guid("{ABC-123}"),
            Some(&"chewing".to_string())
        );
        assert_eq!(registry.resolve_guid("unknown"), None);
    }
}
