Caption "StdUtils Test-Suite"

!addincludedir  "..\..\Include"

!ifdef NSIS_UNICODE
	!addplugindir "..\..\Plugins\Release_Unicode"
	OutFile "TimerCreate-Unicode.exe"
!else
	!addplugindir "..\..\Plugins\Release_ANSI"
	OutFile "TimerCreate-ANSI.exe"
!endif

!include 'StdUtils.nsh'

RequestExecutionLevel user
ShowInstDetails show

Var TimerId
Var MyCount

Function MyCallback
	IntOp $MyCount $MyCount + 1
	DetailPrint "Timer event has been triggered! (#$MyCount)"
FunctionEnd

Function .onGUIInit
	${StdUtils.TimerCreate} $TimerId MyCallback 1500
	StrCmp $TimerId "error" 0 +2
	MessageBox MB_ICONSTOP "Failed to create timer!"
FunctionEnd

Function .onGUIEnd
	StrCmp $TimerId "error" 0 +2
	Return
	${StdUtils.TimerDestroy} $0 $TimerId
	StrCmp $0 "ok" +2
	MessageBox MB_ICONSTOP "Failed to destroy timer!"
FunctionEnd

Section
	DetailPrint "Hello, world!"
SectionEnd
