Caption "StdUtils Test-Suite"

!addincludedir  "..\..\Include"

!ifdef NSIS_UNICODE
	!addplugindir "..\..\Plugins\Release_Unicode"
	OutFile "SHFileOperation-Unicode.exe"
!else
	!addplugindir "..\..\Plugins\Release_ANSI"
	OutFile "SHFileOperation-ANSI.exe"
!endif

!macro NextTest
	Section
		DetailPrint "--------------"
	SectionEnd
!macroend

!include 'StdUtils.nsh'

RequestExecutionLevel user
ShowInstDetails show

# -----------------------------------------
# SHFileCopy/SHFileMove function
# -----------------------------------------

Section
	InitPluginsDir
	SetOutPath "$PLUGINSDIR\TestDirA"
	File "${NSISDIR}\Contrib\Graphics\Checks\*.*"
	SetOutPath "$PLUGINSDIR\TestDirA\SubDir"
	File "${NSISDIR}\Contrib\Graphics\Header\*.*"
	CreateDirectory "$PLUGINSDIR\SubDirX"
	CreateDirectory "$PLUGINSDIR\SubDirY"
	
	${StdUtils.SHFileCopy} $0 "$PLUGINSDIR\TestDirA" "$PLUGINSDIR\SubDirX\TestDirB" $HWNDPARENT
	DetailPrint "SHFileCopy: $0"
	${StdUtils.SHFileMove} $0 "$PLUGINSDIR\TestDirA" "$PLUGINSDIR\SubDirY\TestDirC" $HWNDPARENT
	DetailPrint "SHFileMove: $0"
	ExecShell "explore" "$PLUGINSDIR"
SectionEnd

!insertmacro NextTest

Section
	MessageBox MB_ICONINFORMATION "The next three operations are going to fail!$\nBut only one will be verbose..."

	${StdUtils.SHFileCopy} $0 "$PLUGINSDIR\TestDirXYZ" "$PLUGINSDIR\SubDirX\TestDirZ" $HWNDPARENT
	DetailPrint "SHFileCopy: $0"
	
	${StdUtils.SetVerbose} 1
	${StdUtils.SHFileCopy} $0 "$PLUGINSDIR\TestDirXYZ" "$PLUGINSDIR\SubDirX\TestDirZ" $HWNDPARENT
	DetailPrint "SHFileCopy: $0"
	
	${StdUtils.SetVerbose} 0
	${StdUtils.SHFileCopy} $0 "$PLUGINSDIR\TestDirXYZ" "$PLUGINSDIR\SubDirX\TestDirZ" $HWNDPARENT
	DetailPrint "SHFileCopy: $0"
SectionEnd

!insertmacro NextTest
