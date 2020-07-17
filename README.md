# بسم الله الرحمان الرحيم
# In the name of Allah, the Ever Merciful, Dispenser of Mercy

Arabic (including its dialects) is a language spoken by roughly 440 million native speakers. It is also the language of the Qur'an which extends the importance of this language
to almost a quarter of the world's population. Though one of the main purposes of IMEs are to cater to languages with characters that exceed the number of keys on a keyboard, many people, including native arabic speakers do not have access to keyboards with Arabic characters. This is the case even though arabic keyboard layouts exist.
In order to ease the lives of everyone who needs to type in Arabic using non-Arabic keyboard layouts.

# arabic-ime is an Arabic IME based on the PIME project

Arabic support is not yet implemented, changes coming soon.

[![Build status](https://ci.appveyor.com/api/projects/status/ju8c225nt9qgxeee?svg=true)](https://ci.appveyor.com/project/EasyIME/PIME)
[![GitHub release](https://img.shields.io/github/release/EasyIME/PIME.svg)](https://github.com/EasyIME/PIME/releases)

Implement input methods easily for Windows via Text Services Framework:
*   LibIME contains a library which aims to be a simple wrapper for Windows Text Service Framework (TSF).
*   PIMETextService contains an backbone implementation of Windows text service for using libIME.
*   The python server part requires python 3.x and pywin32 package.

All parts are licensed under GNU LGPL v2.1 license.

# Development
## Tool Requirements
*   [CMake](http://www.cmake.org/) >= 3.0
*   [Visual Studio 2019](https://visualstudio.microsoft.com/vs)
*   [Git](http://windows.github.com/)
*   [NSIS](http://nsis.sourceforge.net/Download)

## How to Build
*   Get source from github.

        git clone https://github.com/ArabicIME/arabic-ime.git
        cd arabic-ime
        git submodule update --init

*   Use the following CMake commands to generate Visual Studio project.

        cmake -G "Visual Studio 16 2019" -A Win32 <path to arabic-ime> -B "build"
        cmake -G "Visual Studio 16 2019" -A x64 <path to arabic-ime> -B "build64"

*   Open a generated project with Visual Studio and build it. You'll need to build both for 64-bit.

## Install
*   Build release version of PIMETextService.dll (both 64 bit and 32 bit versions are required).
*   Compile \<path to arabic-ime\>\installer\installer.nsi with NSIS.
*   Run the installer

## Uninstall
*   Run the uninstaller C:\Program Files (x86)\PIME\Uninstall.exe

## Quick testing of the python code
*   Instead of copying python over to C:\Program Files(x86)\PIME\, create a hardlink to your checked out python folder. Use the following in the PIME directory:

        mklink /J python <path to repo>\arabic-ime\python

*   Restart PIMELauncher to test your changes.

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

# Bug Report
Please report any issue to [here](https://github.com/ArabicIME/arabic-ime/issues).
