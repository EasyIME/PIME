# windows-chewing-tsf

Implement chewing in Windows via Text Services Framework:
*   LibIME contains a library which aims to be a simple wrapper for Windows Text Service Framework (TSF).
*   ChewingTextService contains an implementation of Windows text service for libchewing using libIME.
*   chewingwrapper contains a C++ wrapper for libchewing.

All parts are licensed under GNU LGPL v2.1 license.

# Development

## Tool Requirements
*   [CMake](http://www.cmake.org/) >= 2.8.8
*   [Visual Studio Express 2012](http://www.microsoft.com/visualstudio/eng/products/visual-studio-express-products)
*   [git](http://windows.github.com/)
*   Editor with [EditorConfig](http://editorconfig.org/) supported

## How to Build
*   Get source from github

        git clone https://github.com/chewing/windows-chewing-tsf.git
        cd windows-chewing-tsf
        git submodule init
        git submodule update

*   Use one of the following CMake commands to generate Visual Studio project

        cmake -G "Visual Studio 11" <path to windows-chewing-tsf>
        cmake -G "Visual Studio 11 Win64" <path to windows-chewing-tsf>

*   Open generated project with Visual Studio and build it

## TSF References
*   [Text Services Framework](http://msdn.microsoft.com/en-us/library/windows/desktop/ms629032%28v=vs.85%29.aspx)
*   [Guidelines and checklist for IME development (Windows Store apps)](http://msdn.microsoft.com/en-us/library/windows/apps/hh967425.aspx)
*   [Input Method Editors (Windows Store apps)](http://msdn.microsoft.com/en-us/library/windows/apps/hh967426.aspx)
*   [Third-party input method editors](http://msdn.microsoft.com/en-us/library/windows/desktop/hh848069%28v=vs.85%29.aspx)
*   [Strategies for App Communication between Windows 8 UI and Windows 8 Desktop](http://software.intel.com/en-us/articles/strategies-for-app-communication-between-windows-8-ui-and-windows-8-desktop)
*   [TSF Aware, Dictation, Windows Speech Recognition, and Text Services Framework. (blog)](http://blogs.msdn.com/b/tsfaware/?Redirected=true)
*   [Win32 and COM for Windows Store apps](http://msdn.microsoft.com/en-us/library/windows/apps/br205757.aspx)

## Windows ACL (Access Control List) references
*   [The Windows Access Control Model Part 1](http://www.codeproject.com/Articles/10042/The-Windows-Access-Control-Model-Part-1#SID)
*   [The Windows Access Control Model: Part 2](http://www.codeproject.com/Articles/10200/The-Windows-Access-Control-Model-Part-2#SidFun)
*   [Windows 8 App Container Security Notes - Part 1](http://recxltd.blogspot.tw/2012/03/windows-8-app-container-security-notes.html)
*   [How AccessCheck Works](http://msdn.microsoft.com/en-us/library/windows/apps/aa446683.aspx)
*   [GetAppContainerNamedObjectPath function (enable accessing object outside app containers using ACL)](http://msdn.microsoft.com/en-us/library/windows/desktop/hh448493)
*   [Creating a DACL](http://msdn.microsoft.com/en-us/library/windows/apps/ms717798.aspx)

# Install
*   Copy `ChewingTextService.dll` to C:\Program Files (X86)\ChewingTextService.
*   Copy `libchewing/data/*.dat` to `C:\Program Files (X86)\ChewingTextService\Dictionary`
*   Use `regsvr32` to register `ChewingService.dll`. 64-bit system need to register both 32-bit and 64-bit `ChewingService.dll`

        regsvr32 "C:\Program Files (X86)\ChewingTextService\ChewingTextService.dll" (run as administrator)

*   NOTICE: the `regsvr32` command needs to be run as Administrator. Otherwise you'll get access denied error.
*   In Windows 8, if you put the dlls in places other than C:\Windows or C:\Program Files, they will not be accessible in metro apps.

# For Windows 8, you also need to do this:
*   Create C:\Users\<user_name>\ChewingTextService directory manually before using the input method.
*   Set ACLs for the created directory so it can be accessible from Windows store apps

        cacls C:\Users\<user_name>\ChewingTextService /e /t /g "ALL APPLICATION PACKAGES:f"

*   Warning: this will give full access of this folder to all metro apps. This may not be the optimized permission settings. Further study on ACL is required here.

# Uninstall
*   Remove `%WINDIR%/chewing`
*   Use `regsvr32` to unregister `ChewingTextService.dll`. 64-bit system need to register both 32-bit and 64-bit `ChewingTextService.dll`

        regsvr32 /u "C:\Program Files (X86)\ChewingTextService\ChewingTextService.dll" (run as administrator)

*   NOTICE: the `regsvr32` command needs to be run as Administrator. Otherwise you'll get access denied error.

# Bug Report
Please report any issue to [here](https://github.com/chewing/windows-chewing-tsf/issues).
