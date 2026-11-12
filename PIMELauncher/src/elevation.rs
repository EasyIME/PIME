/// Whether the launcher should surface the elevation warning for this process.
///
/// Only the interactive watchdog instance warns: the worker child inherits the
/// same token, and a second copy of the warning would be pure noise. A normal
/// (non-elevated) run must stay silent.
pub fn should_warn(elevated: bool, is_worker: bool) -> bool {
    elevated && !is_worker
}

/// The user-facing explanation shown when the launcher runs elevated.
///
/// The two `icacls` lines are the repair from issue #973: an elevated first
/// run leaves `%APPDATA%\PIME` owned by `BUILTIN\Administrators`, which a
/// normal session cannot read.
pub fn elevation_advice() -> &'static str {
    "PIMELauncher is running as Administrator.\n\
     \n\
     PIME stores per-user settings and language profiles under %APPDATA%\\PIME. \
     Folders created by this elevated run end up owned by Administrators and \
     become unreadable to your normal session, which silently breaks the input \
     methods (keys stop composing, with no error anywhere).\n\
     \n\
     Quit this instance and restart PIMELauncher as the normal user \u{2014} sign \
     out and in again, or launch it from a non-elevated terminal.\n\
     \n\
     If %APPDATA%\\PIME was already created by an elevated run, repair it from a \
     normal (non-administrator) command prompt:\n\
     \n\
     \x20   icacls \"%APPDATA%\\PIME\" /setowner \"%USERDOMAIN%\\%USERNAME%\" /T\n\
     \x20   icacls \"%APPDATA%\\PIME\" /reset /T"
}

/// Whether this process runs with an elevated (Administrator) token.
///
/// Reads `TokenElevation` from the process token: under UAC a member of the
/// Administrators group gets a filtered token whose `TokenIsElevated` is 0,
/// so this reports the real privilege level rather than group membership.
pub fn is_process_elevated() -> Result<bool, std::io::Error> {
    use std::ffi::c_void;
    use std::mem::size_of;
    use windows::Win32::Foundation::{CloseHandle, HANDLE};
    use windows::Win32::Security::{
        GetTokenInformation, TokenElevation, TOKEN_ELEVATION, TOKEN_QUERY,
    };
    use windows::Win32::System::Threading::{GetCurrentProcess, OpenProcessToken};

    unsafe {
        let mut token = HANDLE::default();
        OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &mut token)
            .map_err(|e| std::io::Error::from_raw_os_error(e.code().0))?;

        let mut elevation = TOKEN_ELEVATION::default();
        let mut returned_length = 0u32;
        let query = GetTokenInformation(
            token,
            TokenElevation,
            Some(&mut elevation as *mut TOKEN_ELEVATION as *mut c_void),
            size_of::<TOKEN_ELEVATION>() as u32,
            &mut returned_length,
        );
        // Close the token before propagating a query failure.
        let _ = CloseHandle(token);
        query.map_err(|e| std::io::Error::from_raw_os_error(e.code().0))?;

        Ok(elevation.TokenIsElevated != 0)
    }
}

/// Logs the elevation warning once, from the watchdog process.
///
/// The warning goes to the `warn` log stream, which reaches the launcher's
/// `/console` window and its `/log-file` sink; a debug log captured while
/// chasing a "keys do nothing" report (issue #973) then carries the cause.
pub fn warn_if_elevated(is_worker: bool) {
    // A failed query must never block the launcher; assume not elevated.
    let elevated = is_process_elevated().unwrap_or(false);
    if !should_warn(elevated, is_worker) {
        return;
    }
    let advice = elevation_advice();
    tracing::warn!("{advice}");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn only_an_elevated_watchdog_warns() {
        assert!(should_warn(true, false), "elevated watchdog must warn");
        assert!(
            !should_warn(true, true),
            "worker child must not duplicate the warning"
        );
        assert!(
            !should_warn(false, false),
            "normal sign-in run must stay silent"
        );
        assert!(!should_warn(false, true));
    }

    #[test]
    fn advice_names_the_repair_from_the_issue() {
        let text = elevation_advice();
        let lowered = text.to_lowercase();
        assert!(
            text.contains("%APPDATA%\\PIME"),
            "must name the poisoned folder"
        );
        assert!(lowered.contains("administrator"), "must name the cause");
        assert!(lowered.contains("icacls"), "must give the repair commands");
        assert!(lowered.contains("/setowner"), "must give the ownership fix");
        assert!(lowered.contains("/reset"), "must give the ACL reset");
        assert!(
            lowered.contains("restart"),
            "must tell the user to relaunch unelevated"
        );
    }

    #[test]
    fn elevation_query_answers_for_current_process() {
        // The TokenElevation query must succeed on the test process itself;
        // the answer depends on how the harness was started, so only the
        // Ok-ness is asserted.
        let _elevated = is_process_elevated().expect("TokenElevation query must succeed");
    }
}
