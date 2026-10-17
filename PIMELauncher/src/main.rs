#![windows_subsystem = "windows"]

use pimelauncher::backend_manager::BackendManager;
use pimelauncher::backend_registry::BackendRegistry;
use pimelauncher::pipe_server;
use std::path::PathBuf;
use tracing::{error, info, warn};

fn get_windows_username() -> String {
    use windows::Win32::System::WindowsProgramming::GetUserNameW;
    use windows::core::PWSTR;
    let mut buf = [0u16; 257];
    let mut size = buf.len() as u32;
    unsafe {
        if GetUserNameW(PWSTR(buf.as_mut_ptr()), &mut size).is_ok() {
            return String::from_utf16_lossy(&buf[..(size as usize).saturating_sub(1)]);
        }
    }
    std::env::var("USERNAME").unwrap_or_else(|_| "Unknown".to_string())
}

fn get_per_session_name(base: &str) -> String {
    let username = get_windows_username();
    format!("Local\\{}_{}", base, username)
}

/// Spawns and monitors the worker process, restarting it if it exits.
async fn run_watchdog(original_args: &[String]) {
    let exe = std::env::current_exe().expect("Failed to get current exe");

    // Prepare worker arguments: keep original args and add /worker
    let mut worker_args: Vec<String> = original_args.iter().skip(1).cloned().collect();
    if !worker_args.iter().any(|arg| arg == "/worker") {
        worker_args.push("/worker".to_string());
    }

    info!("Watchdog started. Monitoring worker...");

    let event_name = get_per_session_name("PIMELauncher2_QuitEvent");
    let (quit_tx, mut quit_rx) = tokio::sync::mpsc::channel::<()>(1);
    
    std::thread::spawn(move || {
        use windows::Win32::Foundation::CloseHandle;
        use windows::Win32::System::Threading::{CreateEventW, WaitForSingleObject, INFINITE};
        
        let mut name_utf16: Vec<u16> = event_name.encode_utf16().collect();
        name_utf16.push(0);
        unsafe {
            if let Ok(handle) = CreateEventW(None, true, false, windows::core::PCWSTR(name_utf16.as_ptr())) {
                let _ = WaitForSingleObject(handle, INFINITE);
                let _ = CloseHandle(handle);
                let _ = quit_tx.blocking_send(());
            }
        }
    });

    const CREATE_NEW_CONSOLE: u32 = 0x00000010;

    loop {
        info!("Spawning worker process...");
        let mut command = tokio::process::Command::new(&exe);
        command.args(&worker_args);

        // If /console was requested, spawn the worker in its own new console window
        if original_args.iter().any(|arg| arg == "/console") {
            command.creation_flags(CREATE_NEW_CONSOLE);
        } else {
            // In background mode, we MUST detach I/O. If we inherit invalid handles
            // (e.g. when running as a service), logging to stdout/stderr can block the process.
            command.stdout(std::process::Stdio::null());
            command.stderr(std::process::Stdio::null());
            command.stdin(std::process::Stdio::null());
        }

        let mut child = match command.spawn() {
            Ok(c) => c,
            Err(e) => {
                error!("Failed to spawn worker process: {}. Retrying in 5s...", e);
                tokio::time::sleep(std::time::Duration::from_secs(5)).await;
                continue;
            }
        };

        tokio::select! {
            status = child.wait() => {
                warn!("Worker process exited with status: {:?}. Restarting in 1s...", status);
                tokio::time::sleep(std::time::Duration::from_secs(1)).await;
            }
            Some(()) = quit_rx.recv() => {
                info!("Quit event received. Terminating worker and watchdog...");
                let _ = child.kill().await;
                return;
            }
        }
    }
}

fn signal_quit_event() {
    use windows::Win32::Foundation::CloseHandle;
    use windows::Win32::System::Threading::{CreateEventW, SetEvent};

    let event_name = get_per_session_name("PIMELauncher2_QuitEvent");
    let mut name_utf16: Vec<u16> = event_name.encode_utf16().collect();
    name_utf16.push(0);

    unsafe {
        // Create or open the event
        if let Ok(handle) = CreateEventW(None, true, false, windows::core::PCWSTR(name_utf16.as_ptr())) {
            let _ = SetEvent(handle);
            let _ = CloseHandle(handle);
            println!("Quit signal sent.");
        }
    }
}

#[derive(Default, Debug)]
struct LauncherArgs {
    is_worker: bool,
    show_console: bool,
    is_quit: bool,
    show_help: bool,
    log_file: Option<String>,
}

impl LauncherArgs {
    fn parse(args: &[String]) -> Self {
        let mut parsed = Self::default();
        let mut iter = args.iter().skip(1);

        while let Some(arg) = iter.next() {
            match arg.as_str() {
                "/worker" => parsed.is_worker = true,
                "/console" => parsed.show_console = true,
                "/quit" => parsed.is_quit = true,
                "/help" | "/?" => parsed.show_help = true,
                "/log-file" => parsed.log_file = iter.next().cloned(),
                _ if arg.starts_with("/log-file=") => {
                    parsed.log_file = arg.split_once('=').map(|(_, v)| v.to_string());
                }
                _ => {}
            }
        }
        parsed
    }
}

fn print_help() {
    use windows::Win32::System::Console::{AttachConsole, ATTACH_PARENT_PROCESS};
    unsafe {
        if AttachConsole(ATTACH_PARENT_PROCESS).is_err() {
            setup_console();
        }
    }
    println!(
        r#"PIMELauncher - Background middleware for PIME text services

USAGE:
    PIMELauncher.exe [OPTIONS]

OPTIONS:
    /console            Open a console window with live DEBUG logs
    /log-file <PATH>    Dump DEBUG logs to the specified file (or /log-file=<PATH>)
    /quit               Gracefully terminate running PIMELauncher instance
    /help, /?           Print this help message
"#
    );
}

fn open_log_file(path_str: &str) -> Option<std::fs::File> {
    let path = std::path::Path::new(path_str);
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    match std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
    {
        Ok(file) => Some(file),
        Err(e) => {
            eprintln!("Failed to open log file {}: {}", path_str, e);
            None
        }
    }
}

fn setup_logging(args: &LauncherArgs) {
    use tracing_subscriber::filter::LevelFilter;
    use tracing_subscriber::layer::SubscriberExt;
    use tracing_subscriber::util::SubscriberInitExt;

    let console_layer = args.show_console.then(|| {
        tracing_subscriber::fmt::layer()
            .with_ansi(true)
            .with_writer(std::io::stdout)
    });

    let file_layer = match &args.log_file {
        Some(path) => open_log_file(path).map(|file| {
            tracing_subscriber::fmt::layer()
                .with_ansi(false)
                .with_writer(std::sync::Mutex::new(file))
        }),
        None => None,
    };

    let level = if console_layer.is_some() || file_layer.is_some() {
        LevelFilter::DEBUG
    } else {
        LevelFilter::WARN
    };

    tracing_subscriber::registry()
        .with(level)
        .with(console_layer)
        .with(file_layer)
        .init();
}

#[tokio::main]
async fn main() {
    assign_process_to_job_object();
    setup_error_mode();

    let raw_args: Vec<String> = std::env::args().collect();
    let args = LauncherArgs::parse(&raw_args);

    if args.show_help {
        print_help();
        return;
    }

    if args.is_quit {
        signal_quit_event();
        return;
    }

    if args.show_console {
        setup_console();
    }

    setup_logging(&args);

    // Ensure single instance (using a named mutex)
    // The Watchdog process (parent) holds this mutex.
    let mutex_name = get_per_session_name("PIMELauncher2_WatchdogMutex");
    let _mutex = if !args.is_worker {
        match create_single_instance_mutex(&mutex_name) {
            Ok(m) => Some(m),
            Err(_) => {
                error!("Another instance of PIMELauncher2 Watchdog is already running.");
                std::process::exit(1);
            }
        }
    } else {
        None
    };

    if !args.is_worker {
        run_watchdog(&raw_args).await;
    } else {
        run_worker().await;
    }
}

/// Creates a Windows Job Object with KILL_ON_JOB_CLOSE and assigns the current process to it.
/// This ensures that when the process exits or is forcefully killed, the OS automatically
/// terminates all of its descendant child processes (workers, backends).
fn assign_process_to_job_object() {
    use windows::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, SetInformationJobObject,
        JobObjectExtendedLimitInformation, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    };
    use windows::Win32::System::Threading::GetCurrentProcess;

    unsafe {
        if let Ok(job) = CreateJobObjectW(None, None) {
            let mut limit_info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
            limit_info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

            let _ = SetInformationJobObject(
                job,
                JobObjectExtendedLimitInformation,
                &limit_info as *const _ as *const std::ffi::c_void,
                std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32,
            );

            let _ = AssignProcessToJobObject(job, GetCurrentProcess());
            // Intentionally leak the `job` handle. It will be closed by the OS when this process exits.
        }
    }
}

/// Disables Windows error reporting dialogs to prevent blocking background processes.
fn setup_error_mode() {
    use windows::Win32::System::Diagnostics::Debug::{
        SetErrorMode, SEM_FAILCRITICALERRORS, SEM_NOALIGNMENTFAULTEXCEPT, SEM_NOGPFAULTERRORBOX,
        SEM_NOOPENFILEERRORBOX,
    };
    unsafe {
        SetErrorMode(
            SEM_FAILCRITICALERRORS
                | SEM_NOGPFAULTERRORBOX
                | SEM_NOALIGNMENTFAULTEXCEPT
                | SEM_NOOPENFILEERRORBOX,
        );
    }
}

/// Core logic for the PIME Worker process.
async fn run_worker() {
    let username = get_windows_username();
    let pipe_name = format!(r"\\.\pipe\{}\PIME\Launcher", username);

    info!("Starting PIMELauncher2 Worker on pipe: {}", pipe_name);

    let pime_root = resolve_pime_root_dir();
    info!("Using PIME root directory: {:?}", pime_root);

    let registry = BackendRegistry::load(&pime_root);
    print_diagnostics(&registry);

    let backend_manager = BackendManager::new(registry);
    let server = pipe_server::PipeServer::new(pipe_name, backend_manager);
    server.run().await;
}

/// Prints available backends and GUID mappings for debugging.
fn print_diagnostics(registry: &BackendRegistry) {
    info!("Available Backends:");
    for (name, config) in &registry.backends {
        info!("  - {}:", name);
        info!("      Command: {}", config.command);
        info!("      Params:  {}", config.params);
        info!("      CWD:     {}", config.working_dir);
    }

    info!("GUID Mappings:");
    for (guid, backend) in &registry.guid_to_backend {
        info!("  {} -> {}", guid, backend);
    }
}

/// Resolves the PIME root directory.
fn resolve_pime_root_dir() -> PathBuf {
    let exe_path = std::env::current_exe().unwrap_or_default();
    let pime_root = exe_path
        .parent()
        .map(|p| p.to_path_buf())
        .unwrap_or_else(|| PathBuf::from("."));

    info!("Executable path: {:?}", exe_path);
    info!("Resolved PIME root: {:?}", pime_root);

    pime_root
}

/// Creates a named mutex to ensure only one instance of the launcher is running.
fn create_single_instance_mutex(
    name: &str,
) -> Result<windows::Win32::Foundation::HANDLE, std::io::Error> {
    use windows::core::PCWSTR;
    use windows::Win32::Foundation::{CloseHandle, GetLastError, ERROR_ALREADY_EXISTS};
    use windows::Win32::System::Threading::CreateMutexW;

    let mut name_utf16: Vec<u16> = name.encode_utf16().collect();
    name_utf16.push(0);

    unsafe {
        match CreateMutexW(None, false, PCWSTR(name_utf16.as_ptr())) {
            Ok(handle) => {
                if let Err(e) = GetLastError() {
                    if e.code() == windows::core::HRESULT::from_win32(ERROR_ALREADY_EXISTS.0) {
                        let _ = CloseHandle(handle);
                        return Err(std::io::Error::from_raw_os_error(
                            ERROR_ALREADY_EXISTS.0 as i32,
                        ));
                    }
                }
                Ok(handle)
            }
            Err(e) => Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                e.to_string(),
            )),
        }
    }
}

/// Allocates a console window and enables ANSI color support.
fn setup_console() {
    use windows::Win32::System::Console::{
        AllocConsole, AttachConsole, GetConsoleMode, GetStdHandle, SetConsoleMode,
        ATTACH_PARENT_PROCESS, ENABLE_VIRTUAL_TERMINAL_PROCESSING, STD_ERROR_HANDLE,
        STD_OUTPUT_HANDLE,
    };
    unsafe {
        // Try to allocate a new console window first (as requested for separate windows)
        if AllocConsole().is_err() {
            // If AllocConsole fails (e.g. already has one), try attaching to parent as fallback
            if AttachConsole(ATTACH_PARENT_PROCESS).is_err() {
                return;
            }
        }

        // Enable ANSI support for both stdout and stderr
        for handle_type in [STD_OUTPUT_HANDLE, STD_ERROR_HANDLE] {
            if let Ok(handle) = GetStdHandle(handle_type) {
                let mut mode = Default::default();
                if GetConsoleMode(handle, &mut mode).is_ok() {
                    mode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
                    let _ = SetConsoleMode(handle, mode);
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_launcher_args_parse() {
        let args1 = vec![
            "PIMELauncher.exe".into(),
            "/console".into(),
            "/log-file".into(),
            "test.log".into(),
        ];
        let p1 = LauncherArgs::parse(&args1);
        assert!(p1.show_console);
        assert_eq!(p1.log_file, Some("test.log".to_string()));
        assert!(!p1.is_worker);
        assert!(!p1.is_quit);
        assert!(!p1.show_help);

        let args2 = vec![
            "PIMELauncher.exe".into(),
            "/log-file=output.log".into(),
            "/worker".into(),
        ];
        let p2 = LauncherArgs::parse(&args2);
        assert!(p2.is_worker);
        assert_eq!(p2.log_file, Some("output.log".to_string()));

        let args3 = vec!["PIMELauncher.exe".into(), "/quit".into()];
        let p3 = LauncherArgs::parse(&args3);
        assert!(p3.is_quit);

        let args4 = vec!["PIMELauncher.exe".into(), "/?".into()];
        let p4 = LauncherArgs::parse(&args4);
        assert!(p4.show_help);

        let args5 = vec!["PIMELauncher.exe".into(), "/help".into()];
        let p5 = LauncherArgs::parse(&args5);
        assert!(p5.show_help);

        let args6 = vec!["PIMELauncher.exe".into(), "/log-file".into()];
        let p6 = LauncherArgs::parse(&args6);
        assert_eq!(p6.log_file, None);
    }
}
