# PIME Stability Fix Progress Checklist

Source Report: `C:\Users\pcman\Downloads\pime_stability_analysis_report.md`  
Scope: Focus primarily on **`PIMELauncher`**, **`PIMETextService`**, and **`libIME2`**, plus essential system/installer fixes. (Excludes bulky third-party distributions in `python/python3` or `node/node_modules`).

---

## P0 (Blocker) - PIMETextService + installer

- [x] **0A.1 / 0A.2 / 2.2 (formerly T6):** Block TSF activation (`IsInteractiveUserLogon`) in `LogonUI.exe` / `winlogon.exe` / `SYSTEM` and fix synchronous pipe hang
  - **Files:** `PIMETextService/PIMEClient.cpp`, `PIMETextService/PIMETextService.cpp`
  - **Details:** Guard against loader lock deadlock and blocking STA thread of `explorer.exe` / `LogonUI.exe`. Fixes **Windows 10 Blank Screen on Boot**.
  - **Verification:** Build / syntax review
  - **Commit:** `47da1bd`

- [x] **0B.1 / 0B.2 / 0B.3:** SignNSIS inner `uninstall.exe` + `nsExec`/`System.dll` plugins, install x86 & x64 VC++ redistributables, and stop `PIMELauncher` before overwriting files
  - **Files:** `installer.nsi`, `.github/workflows/build-and-sign.yaml`
  - **Details:** Fixes **Windows 11 Installation Failures**.
  - **Verification:** Build / syntax review
  - **Commit:** `3d28f08`

---

## P0 (Crash) - PIMELauncher

- [x] **L1 (1.1 - CRITICAL):** Prevent false-positive 15-second hang timeout on client disconnect (`{"method":"close"}`)
  - **Files:** `PIMELauncher/src/backend_manager.rs`, `PIMELauncher/src/protocol.rs`
  - **Details:** Do not set watchdog timer / treat client `close` notification as an RPC expecting a backend response.
  - **Verification:** Unit tests passed (`cargo test --lib`), `cargo check` passed.
  - **Commit:** `8d9261b`

- [x] **L2 (1.2 - CRITICAL):** Close/re-initialize existing client pipe connections when a backend crashes or restarts
  - **Files:** `PIMELauncher/src/backend_manager.rs`, `PIMELauncher/src/pipe_server.rs`
  - **Details:** Avoid leaving clients in a silent brain-dead state after backend recovery.
  - **Verification:** `cargo test` and `cargo check` passed.
  - **Commit:** `04bef1d`

- [x] **L3 (1.3 - HIGH):** Fix hang watchdog race condition with concurrent / pipelined requests
  - **Files:** `PIMELauncher/src/backend_manager.rs`
  - **Details:** Manage request tracking so pipelined requests do not overwrite `last_request_time` and cause premature termination.
  - **Verification:** `cargo check` in `PIMELauncher/`
  - **Commit:** `b925f47`

- [x] **L4 (1.4 - HIGH):** Resolve named pipe server single-listening-instance race window and `is_first_instance` fragility
  - **Files:** `PIMELauncher/src/pipe_server.rs`, `PIMELauncher/src/main.rs`
  - **Details:** Ensure robust pipe listener lifecycle without dropping connections during handoff.
  - **Verification:** `cargo check` in `PIMELauncher/`
  - **Commit:** `ae793f7`

- [x] **L5 (1.5 - HIGH):** Prevent orphaned backend processes (`python.exe`, `node.exe`) using Windows Job Objects
  - **Files:** `PIMELauncher/src/main.rs`, `PIMELauncher/src/backend_manager.rs`
  - **Details:** Assign child processes to a Job Object configured with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`.
  - **Verification:** `cargo check` in `PIMELauncher/`
  - **Commit:** `bc5828e`

- [x] **L6 (1.6 - MEDIUM):** Fix `PIMELauncher2_QuitEvent` manual-reset race condition and add per-session namespace
  - **Files:** `PIMELauncher/src/main.rs`
  - **Details:** Scope IPC event per-session/user and fix manual-reset event race.
  - **Verification:** `cargo check` in `PIMELauncher/`
  - **Commit:** `e14e6cd`

- [x] **L7 (1.7 - MEDIUM):** Fix parameter parsing breaking paths with spaces in `create_backend_process`
  - **Files:** `PIMELauncher/src/backend_manager.rs`
  - **Details:** Avoid naive `split_whitespace()` for executable arguments.
  - **Verification:** `cargo check` in `PIMELauncher/`
  - **Commit:** `0baf5ba`

---

## P0 (Crash) - libIME2 / PIMETextService

- [x] **T1 (Stage 2.1 - CRITICAL):** Fix stack memory corruption / use-after-free on `OVERLAPPED` structure after `WaitForSingleObject` timeout
  - **Files:** `PIMETextService/PIMEClient.cpp`
  - **Details:** Cancel pending IO with `CancelIoEx` before stack buffer is destroyed.
  - **Verification:** C++ syntax review
  - **Commit:** `4f28d50`

- [x] **T2 (Stage 2.2 - CRITICAL):** Fix out-of-bounds heap read & UTF-16 surrogate indexing in `Client::updateComposition`
  - **Files:** `PIMETextService/PIMEClient.cpp`
  - **Details:** Validate UTF-16 code unit bounds when calculating cursor and clause offsets.
  - **Verification:** C++ syntax review
  - **Commit:** `53045a4`

- [x] **T3 (Stage 2.3 - CRITICAL):** Fix out-of-bounds read on `selKeys_[i]` when `candidates_.size() > selKeys_.size()`
  - **Files:** `PIMETextService/PIMETextService.cpp`
  - **Details:** Guard selection key indexing against candidate count.
  - **Verification:** C++ syntax review
  - **Commit:** `dbe4e68`

- [x] **T4 (Stage 2.4 - CRITICAL):** Catch `nlohmann::json::exception` across COM boundaries to prevent host app crashes
  - **Files:** `PIMETextService/PIMEClient.cpp`
  - **Details:** Wrap JSON parsing and property extraction in `try/catch` and return `E_FAIL` instead of crashing host processes.
  - **Verification:** C++ syntax review
  - **Commit:** `38a2766`

- [x] **T5 (Stage 2.8 - HIGH):** Fix `WaitNamedPipe` failure when pipe does not exist yet & fast 3-attempt failure
  - **Files:** `PIMETextService/PIMEClient.cpp`
  - **Details:** Implement proper retry/backoff when pipe server is starting up.
  - **Verification:** C++ syntax review
  - **Commit:** `7cc28ad`

- [x] **M1 (Stage 2.5 - CRITICAL):** Fix thread-unsafe process-wide statics (`Window::hwndMap_`, `iconCache_`) and cross-thread `HICON` destruction
  - **Files:** `libIME2/src/Window.cpp`, `libIME2/src/LangBarButton.cpp`
  - **Details:** Synchronize shared maps or use thread-local / instance mappings.
  - **Verification:** C++ syntax review
  - **Commit:** `5d18c0b`

- [x] **M2 (Stage 2.6 - HIGH):** Fix null pointer dereferences in `CandidateWindow::GetDocumentMgr` & `TextService::globalCompartment`
  - **Files:** `libIME2/src/CandidateWindow.cpp`, `libIME2/src/TextService.cpp`
  - **Details:** Check pointers before dereferencing.
  - **Verification:** C++ syntax review
  - **Commit:** `4e48ad2`

- [x] **M3 (Stage 2.7 - HIGH):** Fix integer underflow (`items_.size() - 1`) and division-by-zero in `CandidateWindow`
  - **Files:** `libIME2/src/CandidateWindow.cpp`
  - **Details:** Guard empty candidate list and zero page size in `recalculateSize`.
  - **Verification:** C++ syntax review
  - **Commit:** `d404876`

- [x] **M4 (Stage 2.9 - MEDIUM):** Fix COM reference cycles (`TextService` <-> `LangBarButton`) and `OnTestKeyUp` event type bug
  - **Files:** `libIME2/src/LangBarButton.cpp`, `libIME2/src/TextService.cpp`
  - **Details:** Break cycle on deactivation and fix return types.
  - **Verification:** C++ syntax review
  - **Commit:** `11c5c16`

- [x] **M5 (Part 0A.3 / 0B.5):** Fix `DllRegisterServer` failing on `Default User\ntuser.dat` and `HKEY_USERS` enumeration
  - **Files:** `libIME2/src/ImeModule.cpp`
  - **Details:** Gracefully handle legacy path failures and missing profile directories.
  - **Verification:** C++ syntax review
  - **Commit:** `22b63ee`

---

## Stage 3 - Python & Node.js Backends (P1/P2)

### 3A: Python Backend
- [x] **3A.1 (CRITICAL):** Fix tight busy-wait spin loop (`while CinTable.loading: continue`) and thread-unsafe shared `CinTable`
- [x] **3A.2 (CRITICAL):** Fix `ChewingConfig.save()` shadowing the `json` module, which truncates `config.json` to 0 bytes
- [x] **3A.3 (CRITICAL):** Fix exception fallback in `server.py` omitting `"seqNum"` and leaving dirty `self.currentReply` state
- [ ] **3A.4 (HIGH):** Fix process-wide `rime.finalize()` killing active Rime sessions in other apps and blocking module import
- [ ] **3A.5 (HIGH):** Fix out-of-bounds `IndexError` and unclosed SQLite connections in `ChewingTextService`
- [ ] **3A.6 (HIGH):** Fix broken `GetAsyncKeyState`/`GetKeyState` in headless `python.exe` and `CinBaseConfig` singleton bug

### 3B: Node.js Backend
- [ ] **3B.1 (CRITICAL):** Fix `line.split('|', 2)` truncating JSON payloads containing pipe characters, crashing `node.exe`
- [ ] **3B.2 (CRITICAL):** Fix JavaScript default parameter pitfall in `requestHandler.js` crashing when `service === null`
- [ ] **3B.3 (HIGH):** Fix unprotected synchronous file I/O (`fs.readFileSync`, `JSON.parse`) in `loadServices.js` crashing on startup
- [ ] **3B.4 (MEDIUM):** Fix stale `candidateCursor` out-of-bounds crash and broken selection key logic in `emojime`
