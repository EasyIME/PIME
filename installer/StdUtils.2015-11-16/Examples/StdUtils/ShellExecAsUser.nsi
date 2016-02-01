Caption "StdUtils Test-Suite"

!addincludedir  "..\..\Include"

!ifdef NSIS_UNICODE
	!addplugindir "..\..\Plugins\Release_Unicode"
	OutFile "ShellExecAsUser-Unicode.exe"
!else
	!addplugindir "..\..\Plugins\Release_ANSI"
	OutFile "ShellExecAsUser-ANSI.exe"
!endif

!include 'StdUtils.nsh'

RequestExecutionLevel admin ;make sure our installer will get elevated on Vista+ with UAC enabled
ShowInstDetails show

Section
	DetailPrint 'ExecShell: "$SYSDIR\mspaint.exe"'
	ExecShell "open" "$SYSDIR\mspaint.exe" ;this instance of MS Paint will be elevated too!
	MessageBox MB_TOPMOST "Close Paint and click 'OK' to continue..."
SectionEnd

Section
	DetailPrint 'ExecShellAsUser: "$SYSDIR\mspaint666.exe"'
	Sleep 1000
	${StdUtils.ExecShellAsUser} $0 "$SYSDIR\mspaint666.exe" "open" "" ;launch a *non-elevated* instance of MS Paint
	DetailPrint "Result: $0" ;expected result is "ok" on UAC-enabled systems or "fallback" otherwise. Failure indicated by "error" or "timeout".
SectionEnd

Section
	DetailPrint 'ExecShellAsUser: "$SYSDIR\mspaint.exe"'
	Sleep 1000
	${StdUtils.ExecShellAsUser} $0 "$SYSDIR\mspaint.exe" "open" "" ;launch a *non-elevated* instance of MS Paint
	DetailPrint "Result: $0" ;expected result is "ok" on UAC-enabled systems or "fallback" otherwise. Failure indicated by "error" or "timeout".
SectionEnd
