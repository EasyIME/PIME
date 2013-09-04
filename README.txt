LibIME contains a library which aims to be a simple wrapper for Windows Text Service Framework (TSF).

ChewingTextService contains an implementation of Windows text service for libchewing using libIME.

Both parts are licensed under GNU LGPL license.

How to Build:

Initial and synchronize submodule libchewing
- git submodule init
- git submodule update

Use CMake to generate Visual Studio project file
- cmake -G "Visual Studio 10" <path to windows-chewing-tsf> (Visual Studio 2010 for x86)
- cmake -G "Visual Studio 10 Win64" <path to windows-chewing-tsf> (Visual Studio 2010 for x64)

Build project with Visual Studio

Copy libchewing/data/*.dat to %WINDIR%/chewing.

Use regsvr32 to register ChewingTextService.dll (In Debug folder if configure is Debug).
- regsvr32 ChewingTextService.dll

NOTICE: the regsvr32 command needs to be run as Administrator.
Otherwise you'll get access denied error.
