# PIME

[![Build status](https://ci.appveyor.com/api/projects/status/ju8c225nt9qgxeee?svg=true)](https://ci.appveyor.com/project/EasyIME/PIME)
[![GitHub release](https://img.shields.io/github/release/EasyIME/PIME.svg)](https://github.com/EasyIME/PIME/releases)

Implement input methods easily for Windows via Text Services Framework:
*   LibIME contains a library which aims to be a simple wrapper for Windows Text Service Framework (TSF).
*   PIMETextService contains an backbone implementation of Windows text service for using libIME.
*   The python server part requires python 3.x and pywin32 package.

All parts are licensed under GNU LGPL v2.1 license.

# Contributing
Contributions using AI coding tools are welcomed! However, to ensure code quality, they must follow the rules in [AGENTS.md](AGENTS.md) to be accepted, and AI assistance must be clearly declared in pull requests, git commits, and file headers.

# Development

## Tool Requirements
*   [CMake](https://cmake.org/) >= 4.0 (Required for Visual Studio 2026 generator; bundled with Visual Studio 2026 or available via `winget install Kitware.CMake`)
*   [Visual Studio 2026](https://visualstudio.microsoft.com/vs) (with "Desktop development with C++" workload)
    *   **MSVC C++ ARM64/ARM64EC build tools** (Required component in Visual Studio Installer for building the ARM64X forwarder DLL)
    *   **Windows 10/11 SDK**
*   [Rust Toolchain](https://rustup.rs/) (Stable channel with `i686-pc-windows-msvc` target)
*   [git](https://git-scm.com/)
*   [Node.js](https://nodejs.org/) (Required for some backends like McBopomofo)
*   [.NET SDK](https://dotnet.microsoft.com/download) (Required for WiX v4)
*   [WiX Toolset v4](https://wixtoolset.org/) (Install via `dotnet tool install --global wix --version 4.0.6`)

## How to Build
*   Get source from github.

        git clone https://github.com/EasyIME/PIME.git
        cd PIME
        git submodule update --init

*   Ensure the 32-bit Rust target is installed:

        rustup target add i686-pc-windows-msvc

*   Use `build.bat` to build everything, or use the following CMake commands to generate Visual Studio project:

        cmake . -Bbuild -G "Visual Studio 18 2026" -A Win32 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
        cmake --build build --config Release

        # For 64-bit Text Service (Required for 64-bit apps)
        cmake . -Bbuild64 -G "Visual Studio 18 2026" -A x64 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
        cmake --build build64 --config Release --target PIMETextService

        # For ARM64 Text Service (Required for ARM64/ARM64X apps)
        cmake . -Bbuild_arm64 -G "Visual Studio 18 2026" -A ARM64 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
        cmake --build build_arm64 --config Release --target PIMETextService

*   To build the installer, ensure the WiX Toolset v4 CLI is installed (`dotnet tool install --global wix --version 4.0.6`). Then run `build.bat` or:

        dotnet build installer/PIME_WiX.sln -c Release
        installer\build_multilingual.bat

    The generated multilingual MSI package will be created at `installer/bin/PIME_Core_Multilingual.msi`.

## TSF References
*   [Text Services Framework](http://msdn.microsoft.com/en-us/library/windows/desktop/ms629032%28v=vs.85%29.aspx)
*   [Guidelines and checklist for IME development (Windows Store apps)](http://msdn.microsoft.com/en-us/library/windows/apps/hh967425.aspx)
*   [Input Method Editors (Windows Store apps)](http://msdn.microsoft.com/en-us/library/windows/apps/hh967426.aspx)
*   [Third-party input method editors](http://msdn.microsoft.com/en-us/library/windows/desktop/hh848069%28v=vs.85%29.aspx)
*   [Strategies for App Communication between Windows 8 UI and Windows 8 Desktop](http://software.intel.com/en-us/articles/strategies-for-app-communication-between-windows-8-ui-and-windows-8-desktop)
*   [TSF Aware, Dictation, Windows Speech Recognition, and Text Services Framework. (blog)](http://blogs.msdn.com/b/tsfaware/?Redirected=true)
*   [Win32 and COM for Windows Store apps](http://msdn.microsoft.com/en-us/library/windows/apps/br205757.aspx)
*   [Input Method Editor (IME) sample supporting Windows 8](http://code.msdn.microsoft.com/windowsdesktop/Input-Method-Editor-IME-b1610980)

## Windows ACL (Access Control List) references
*   [The Windows Access Control Model Part 1](http://www.codeproject.com/Articles/10042/The-Windows-Access-Control-Model-Part-1#SID)
*   [The Windows Access Control Model: Part 2](http://www.codeproject.com/Articles/10200/The-Windows-Access-Control-Model-Part-2#SidFun)
*   [Windows 8 App Container Security Notes - Part 1](http://recxltd.blogspot.tw/2012/03/windows-8-app-container-security-notes.html)
*   [How AccessCheck Works](http://msdn.microsoft.com/en-us/library/windows/apps/aa446683.aspx)
*   [GetAppContainerNamedObjectPath function (enable accessing object outside app containers using ACL)](http://msdn.microsoft.com/en-us/library/windows/desktop/hh448493)
*   [Creating a DACL](http://msdn.microsoft.com/en-us/library/windows/apps/ms717798.aspx)

# Install
*   Copy `PIMETextService.dll` to C:\Program Files (X86)\PIME\x86\.
*   Copy `PIMETextService.dll` to C:\Program Files (X86)\PIME\x64\.
*   Copy the folder `python` to `C:\Program Files (X86)\PIME\`
*   Copy the folder `node` to `C:\Program Files (X86)\PIME\`
*   Use `regsvr32` to register `PIMETextService.dll`. 64-bit system need to register both 32-bit and 64-bit `PIMETextService.dll`

        regsvr32 "C:\Program Files (X86)\PIME\x86\PIMETextService.dll" (run as administrator)
        regsvr32 "C:\Program Files (X86)\PIME\x64\PIMETextService.dll" (run as administrator)

*   NOTICE: the `regsvr32` command needs to be run as Administrator. Otherwise you'll get access denied error.
*   In Windows 8, if you put the dlls in places other than C:\Windows or C:\Program Files, they will not be accessible in metro apps.

# Uninstall
*   Use `regsvr32` to unregister `PIMETextService.dll`. 64-bit system need to unregister both 32-bit and 64-bit `PIMETextService.dll`

        regsvr32 /u "C:\Program Files (X86)\PIME\x86\PIMETextService.dll" (run as administrator)
        regsvr32 /u "C:\Program Files (X86)\PIME\x64\PIMETextService.dll" (run as administrator)
*   Remove `C:\Program Files (X86)\PIME`

*   NOTICE: the `regsvr32` command needs to be run as Administrator. Otherwise you'll get access denied error.

# Bug Report
Please report any issue to [here](https://github.com/EasyIME/PIME/issues).

# Debugging
If you encounter issues, you can run `PIMELauncher.exe` with the following debugging options:

* **Live console output**:
  ```powershell
  PIMELauncher.exe /console
  ```
  Opens a console window displaying live `DEBUG` level logs for troubleshooting backend communication and internal events.

* **Log to file (headless)**:
  ```powershell
  PIMELauncher.exe /log-file C:\path\to\pime.log
  ```
  Writes `DEBUG` level logs to the specified file while running silently in the background without popping up a console window.

* **Quit running instance**:
  ```powershell
  PIMELauncher.exe /quit
  ```

* **Show help message**:
  ```powershell
  PIMELauncher.exe /help
  # or: PIMELauncher.exe /?
  ```

When run normally without `/console` or `/log-file`, all debug logging is completely suppressed to avoid unnecessary I/O overhead.
