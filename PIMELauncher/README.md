# PIMELauncher

PIMELauncher is a high-performance, Rust-based background service for **PIME** (Platform for Input Method Editors). It serves as a robust proxy for communication between Text Services Framework (TSF) clients and various input method backend processes.

## Key Features

- **Robust Proxying:** Seamlessly forwards communication between TSF clients and backend input methods.
- **Lifecycle Management:** Automatically spawns, monitors, and restarts backend processes if they crash or hang.
- **Async Architecture:** Built on [Tokio](https://tokio.rs/), ensuring non-blocking I/O and high concurrency.

## Architecture

PIMELauncher is designed with modularity in mind:
- **Pipe Server:** Handles incoming client connections via named pipes (`\\.\pipe\<user>\PIME\Launcher`).
- **Backend Manager:** Manages the lifecycle of backend processes (Python, Node.js, etc.) and routes messages.
- **Registry:** Dynamically loads backend configurations from `backends.json` and maps TSF GUIDs via `ime.json` discovery.
- **Protocol:** Uses a line-based UTF-8 JSON protocol for easy integration and debugging.

## Build Instructions

### Prerequisites

- **Windows OS:** Required for named pipes and Windows API integrations.
- **Rust Toolchain:** Install via [rustup.rs](https://rustup.rs/) (Stable channel recommended).
- **32-bit Target:** Ensure you have the 32-bit MSVC target installed:
  ```powershell
  rustup target add i686-pc-windows-msvc
  ```

### Integrated Build (Recommended)

PIMELauncher is integrated into the main PIME build system via **CMake** and **Corrosion**. To build everything (including the launcher and installer), run the root build script:

```powershell
# From the project root
.\build.bat
```

The compiled binary will be automatically placed at `build\PIMELauncher\PIMELauncher.exe`, which is the location expected by the NSIS installer.

### Manual Build (For Development)

You can still build the launcher independently for development purposes:

```powershell
cd PIMELauncher
cargo build --release --target i686-pc-windows-msvc
```

*Note: Manual cargo builds will place the binary in `PIMELauncher/target/i686-pc-windows-msvc/release/PIMELauncher.exe`.*

## Usage

### Running the Service
PIMELauncher is typically started automatically by the PIME Text Service. However, it can be run manually for debugging:

```powershell
# If built via CMake
.\build\PIMELauncher\PIMELauncher.exe

# If built via Cargo
.\PIMELauncher\target\i686-pc-windows-msvc\release\PIMELauncher.exe
```

### Named Pipe
The service listens on: `\\.\pipe\<CURRENT_USER_NAME>\PIME\Launcher`

## Testing

The project includes an extensive test suite, including integration tests that simulate client-server-backend communication.

```powershell
# From the PIMELauncher directory
cargo test
```

## AI Disclosure & Acknowledgments

This project was developed with the assistance of **Gemini** (a generative AI model by Google DeepMind).

### Development Model
The development of PIMELauncher followed a "Human-in-the-Loop" approach:
- **System Design & Architecture:** The modular architecture, structural decoupling, and service lifecycle were designed by Hong Jen Yee (PCMan).
- **AI Knowledge Transfer:** The AI assistant was provided with the original **PIMELauncher C++ implementation** (authored by PCMan) as a reference. The AI learned and adapted these architectural concepts to the Rust rewrite under strict human guidance.
- **Protocol Specification:** The communication protocol and handshake logic were manually defined to ensure system integrity and compatibility.
- **AI-Assisted Coding:** Gemini was used for boilerplate generation, implementing initial drafts of core modules, and writing the test suite.
- **Test Case Design:** The test logic and scenarios were entirely designed by PCMan, while the implementation was handled by the AI.
- **Verification & Modification:** Every line of code was audited, tested, and significantly modified by the human author to ensure it aligns with the intended design and project requirements.

### Copyright and Ownership
Hong Jen Yee (PCMan) retains full copyright and responsibility for the system design and the final code implementation. The AI tools were utilized as an advanced development environment (IDE) enhancement rather than as an independent author.
