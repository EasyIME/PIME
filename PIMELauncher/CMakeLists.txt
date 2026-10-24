corrosion_import_crate(MANIFEST_PATH Cargo.toml)

# Rust links the MSVC CRT dynamically by default. PIME ships no VC++
# redistributable, so link it statically like the C++ targets (/MT).
corrosion_add_target_rustflags(PIMELauncher "-Ctarget-feature=+crt-static")
