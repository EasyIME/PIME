Caption "StdUtils Test-Suite"

!addincludedir  "..\..\Include"

!ifdef NSIS_UNICODE
	!addplugindir "..\..\Plugins\Release_Unicode"
	OutFile "ShellExecWait-Unicode.exe"
!else
	!addplugindir "..\..\Plugins\Release_ANSI"
	OutFile "ShellExecWait-ANSI.exe"
!endif

!include 'StdUtils.nsh'

RequestExecutionLevel user
ShowInstDetails show

Section
	DetailPrint 'ExecShellWait: "$SYSDIR\mspaint.exe"'
	Sleep 1000
	${StdUtils.ExecShellWaitEx} $0 $1 "$SYSDIR\mspaint.exe" "open" "" ;try to launch the process

	DetailPrint "Result: $0 -> $1" ;returns "ok", "no_wait" or "error".
	StrCmp $0 "error" ExecFailed ;check if process failed to create
	StrCmp $0 "no_wait" WaitNotPossible ;check if process can be waited for - always check this!
	StrCmp $0 "ok" WaitForProc ;make sure process was created successfully
	Abort
	
	WaitForProc:
	DetailPrint "Waiting for process. ZZZzzzZZZzzz..."
	${StdUtils.WaitForProcEx} $2 $1
	DetailPrint "Process just terminated (exit code: $2)"
	Goto WaitDone
	
	ExecFailed:
	DetailPrint "Failed to create process (error code: $1)"
	Goto WaitDone

	WaitNotPossible:
	DetailPrint "Can not wait for process."
	Goto WaitDone
	
	WaitDone:
SectionEnd
