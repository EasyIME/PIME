Caption "StdUtils Test-Suite"

!addincludedir  "..\..\Include"

!ifdef NSIS_UNICODE
	!addplugindir "..\..\Plugins\Release_Unicode"
	OutFile "AppendToFile-Unicode.exe"
!else
	!addplugindir "..\..\Plugins\Release_ANSI"
	OutFile "AppendToFile-ANSI.exe"
!endif

!include 'StdUtils.nsh'

RequestExecutionLevel user
ShowInstDetails show

Section
	${StdUtils.AppendToFile} $0 "$WINDIR\Explorer.exe" "$TEMP\Combined.exe" 0 0
	DetailPrint "AppendToFile: $0"
	
	${StdUtils.AppendToFile} $0 "$WINDIR\Notepad.exe"  "$TEMP\Combined.exe" 0 0
	DetailPrint "AppendToFile: $0"
SectionEnd
