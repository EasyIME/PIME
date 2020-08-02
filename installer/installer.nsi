;
;	Copyright (C) 2013 - 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
;
;	This library is free software; you can redistribute it and/or
;	modify it under the terms of the GNU Library General Public
;	License as published by the Free Software Foundation; either
;	version 2 of the License, or (at your option) any later version.
;
;	This library is distributed in the hope that it will be useful,
;	but WITHOUT ANY WARRANTY; without even the implied warranty of
;	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;	Library General Public License for more details.
;
;	You should have received a copy of the GNU Library General Public
;	License along with this library; if not, write to the
;	Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
;	Boston, MA  02110-1301, USA.
;

!include "MUI2.nsh" ; modern UI
!include "x64.nsh" ; NSIS plugin used to detect 64 bit Windows
!include "Winver.nsh" ; Windows version detection
!include "LogicLib.nsh" ; for ${If}, ${Switch} commands

; We need the StdUtils plugin
!addincludedir "StdUtils.2015-11-16\Include"
!addplugindir /x86-unicode "StdUtils.2015-11-16\Plugins\Release_Unicode"
!include "StdUtils.nsh" ; for ExecShellAsUser()

; We need the MD5 plugin
!addplugindir /x86-unicode "md5dll\UNICODE"

Unicode true ; turn on Unicode (This requires NSIS 3.0)
SetCompressor /SOLID lzma ; use LZMA for best compression ratio
SetCompressorDictSize 16 ; larger dictionary size for better compression ratio
AllowSkipFiles off ; cannot skip a file

; We need the Replace in file plugin
!addincludedir "utils"
!include "StrRep.nsh"
!include "ReplaceInFile.nsh"

; icons of the generated installer and uninstaller
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall.ico"

!define /file PRODUCT_VERSION "..\version.txt"

!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\PIME"
!define HOMEPAGE_URL "https://github.com/ArabicIME/arabic-ime"

Name "$(PRODUCT_NAME)"
BrandingText "$(PRODUCT_NAME)"

OutFile "PIME-${PRODUCT_VERSION}-setup.exe" ; The generated installer file name

; We install everything to C:\Program Files (x86)
InstallDir "$PROGRAMFILES32\PIME"

;Request application privileges (need administrator to install)
RequestExecutionLevel admin
!define MUI_ABORTWARNING

;Pages
; license page
!insertmacro MUI_PAGE_LICENSE "..\LGPL-2.0.txt" ; for PIME
!insertmacro MUI_PAGE_LICENSE "..\PSF.txt" ; for python

; !insertmacro MUI_PAGE_COMPONENTS
!define MUI_COMPONENTSPAGE_SMALLDESC
!insertmacro MUI_PAGE_COMPONENTS

; installation progress page
!insertmacro MUI_PAGE_INSTFILES

; finish page
!insertmacro MUI_PAGE_FINISH

; uninstallation pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
;--------------------------------

!macro LANG_LOAD LANGLOAD
  !insertmacro MUI_LANGUAGE "${LANGLOAD}"
  !include "locale\${LANGLOAD}.nsh"
  !undef LANG
!macroend

!macro LANG_STRING NAME VALUE
  LangString "${NAME}" "${LANG_${LANG}}" "${VALUE}"
!macroend

!macro LANG_UNSTRING NAME VALUE
  !insertmacro LANG_STRING "un.${NAME}" "${VALUE}"
!macroend

!insertmacro LANG_LOAD "English" ; English

var UPDATEX86DLL
var UPDATEX64DLL

var INST_PYTHON

; Uninstall old versions
Function uninstallOldVersion
	ClearErrors
	;  run uninstaller
	ReadRegStr $R0 HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
	${If} $R0 != ""
		ClearErrors
		${If} ${FileExists} "$INSTDIR\Uninstall.exe"
			MessageBox MB_OKCANCEL|MB_ICONQUESTION $(UNINSTALL_OLD) IDOK +2
			Abort ; this is skipped if the user select OK

			; Remove the launcher from auto-start
			DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PIME"
			DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "PIMELauncher"
			DeleteRegKey /ifempty HKLM "Software\PIME"

			; Unregister COM objects (NSIS UnRegDLL command is broken and cannot be used)
			ExecWait '"$SYSDIR\regsvr32.exe" /u /s "$INSTDIR\x86\PIMETextService.dll"'
			; Verify the MD5/SHA1 checksum of 32-bit PIMETextService.dll
			StrCpy $0 "$INSTDIR\x86\PIMETextService.dll"
			md5dll::GetMD5File "$0"
			Pop $1
			StrCpy $2 "$PLUGINSDIR\PIMETextService_x86.dll"
			md5dll::GetMD5File "$2"
			Pop $3
			${If} $1 == $3
				StrCpy $UPDATEX86DLL "False"
			${Else}
				RMDir /REBOOTOK /r "$INSTDIR\x86"
			${EndIf}

			${If} ${RunningX64}
				SetRegView 64 ; disable registry redirection and use 64 bit Windows registry directly
				ExecWait '"$SYSDIR\regsvr32.exe" /u /s "$INSTDIR\x64\PIMETextService.dll"'
				; Verify the MD5/SHA1 checksum of 64-bit PIMETextService.dll
				StrCpy $0 "$INSTDIR\x64\PIMETextService.dll"
				md5dll::GetMD5File "$0"
				Pop $1
				StrCpy $2 "$PLUGINSDIR\PIMETextService_x64.dll"
				md5dll::GetMD5File "$2"
				Pop $3
				${If} $1 == $3
					StrCpy $UPDATEX64DLL "False"
				${Else}
					RMDir /REBOOTOK /r "$INSTDIR\x64"
				${EndIf}
			${EndIf}

			; Try to terminate running PIMELauncher and the server process
			; Otherwise we cannot replace it.
			ExecWait '"$INSTDIR\PIMELauncher.exe" /quit'

			Delete /REBOOTOK "$INSTDIR\PIMELauncher.exe"

            Delete "$INSTDIR\backends.json"
			RMDir /REBOOTOK /r "$INSTDIR\python"

			; Only exist in earlier versions, but need to delete it.
			RMDir /REBOOTOK /r "$INSTDIR\server"

			; Delete shortcuts
			Delete "$SMPROGRAMS\$(PRODUCT_NAME)\$(UNINSTALL_PIME).lnk"
			RMDir "$SMPROGRAMS\$(PRODUCT_NAME)"

			Delete "$INSTDIR\version.txt"
			Delete "$INSTDIR\Uninstall.exe"
			RMDir "$INSTDIR"

			${If} ${RebootFlag}
				MessageBox MB_YESNO "$(MB_REBOOT_REQUIRED)" IDNO +3
				Reboot
				Quit
				Abort
			${EndIf}
		${EndIf}
	${EndIf}

	ClearErrors
	; Ensure that old files are all deleted
	${If} ${RunningX64}
		${If} ${FileExists} "$INSTDIR\x64\PIMETextService.dll"
			; Verify the MD5/SHA1 checksum of 64-bit PIMETextService.dll
			StrCpy $0 "$INSTDIR\x64\PIMETextService.dll"
			md5dll::GetMD5File "$0"
			Pop $1
			StrCpy $2 "$PLUGINSDIR\PIMETextService_x64.dll"
			md5dll::GetMD5File "$2"
			Pop $3
			${If} $1 == $3
				StrCpy $UPDATEX64DLL "False"
			${Else}
				Delete /REBOOTOK "$INSTDIR\x64\PIMETextService.dll"
				IfErrors 0 +2
					Call .onInstFailed
			${EndIf}
		${EndIf}
	${EndIf}

	${If} ${FileExists} "$INSTDIR\x86\PIMETextService.dll"
		; Verify the MD5/SHA1 checksum of 32-bit PIMETextService.dll
		StrCpy $0 "$INSTDIR\x86\PIMETextService.dll"
		md5dll::GetMD5File "$0"
		Pop $1
		StrCpy $2 "$PLUGINSDIR\PIMETextService_x86.dll"
		md5dll::GetMD5File "$2"
		Pop $3
		${If} $1 == $3
			StrCpy $UPDATEX86DLL "False"
		${Else}
			Delete /REBOOTOK "$INSTDIR\x86\PIMETextService.dll"
			IfErrors 0 +2
				Call .onInstFailed
		${EndIf}
	${EndIf}

	${If} ${RebootFlag}
		Call .onInstFailed
	${EndIf}
FunctionEnd

; Called during installer initialization
Function .onInit
	;Language selection dialog

	Push ""
	Push ${LANG_ENGLISH}
	Push "English"
	Push A ; A means auto count languages
	       ; for the auto count to work the first empty push (Push "") must remain
	LangDLL::LangDialog $(INSTALLER_LANGUAGE_TITLE) $(INSTALL_LANGUAGE_MESSAGE)

	Pop $LANGUAGE
	StrCmp $LANGUAGE "cancel" 0 +2
		Abort
	; Currently, we're not able to support Windows xp since it has an incomplete TSF.
	${IfNot} ${AtLeastWinVista}
		MessageBox MB_ICONSTOP|MB_OK $(AtLeastWinVista_MESSAGE)
		Quit
	${EndIf}

	${If} ${RunningX64}
		SetRegView 64 ; disable registry redirection and use 64 bit Windows registry directly
	${EndIf}

	File "/oname=$PLUGINSDIR\PIMETextService_x86.dll" "..\build\PIMETextService\Release\PIMETextService.dll"
	File "/oname=$PLUGINSDIR\PIMETextService_x64.dll" "..\build64\PIMETextService\Release\PIMETextService.dll"

	StrCpy $UPDATEX86DLL "True"
	StrCpy $UPDATEX64DLL "True"

	StrCpy $INST_PYTHON "False"

	; check if old version is installed and uninstall it first
	Call uninstallOldVersion
FunctionEnd

; called to show an error message when errors happen
Function .onInstFailed
	${If} ${RebootFlag}
		MessageBox MB_YESNO $(REBOOT_QUESTION) IDNO +3
		Reboot
		Quit
		Abort
	${Else}
		MessageBox MB_ICONSTOP|MB_OK $(INST_FAILED_MESSAGE)
		Abort
	${EndIf}
FunctionEnd

Function ensureVCRedist
    ; Check if we have Universal CRT (provided by VC++ 2015 runtime)
    ; Reference: https://blogs.msdn.microsoft.com/vcblog/2015/03/03/introducing-the-universal-crt/
    ;            https://docs.python.org/3/using/windows.html#embedded-distribution
    ${IfNot} ${FileExists} "$SYSDIR\ucrtbase.dll"
	${OrIfNot} ${FileExists} "$SYSDIR\msvcp140.dll"
        MessageBox MB_YESNO|MB_ICONQUESTION $(DOWNLOAD_VC2015_QUESTION) IDYES +2
            Abort ; this is skipped if the user select Yes
        ; Download VC++ 2015 redistibutable (x86 version)
        nsisdl::download "http://download.microsoft.com/download/9/3/F/93FCF1E7-E6A4-478B-96E7-D4B285925B00/vc_redist.x86.exe" "$TEMP\vc2015_redist.x86.exe"
        Pop $R0 ;Get the return value
        ${If} $R0 != "success"
            MessageBox MB_ICONSTOP|MB_OK $(DOWNLOAD_VC2015_FAILED_MESSAGE)
            Abort
        ${EndIf}

        ; Run vcredist installer
        ExecWait "$TEMP\vc2015_redist.x86.exe" $0

        ; check again if ucrtbase.dll or msvcp140.dll is available
        ${IfNot} ${FileExists} "$SYSDIR\ucrtbase.dll"
		${OrIfNot} ${FileExists} "$SYSDIR\msvcp140.dll"
            MessageBox MB_ICONSTOP|MB_OK $(INST_VC2015_FAILED_MESSAGE)
            ExecShell "open" "https://support.microsoft.com/en-us/kb/2999226"
            Abort
        ${EndIf}
    ${EndIf}
FunctionEnd

;Installer Type
InstType "$(INST_TYPE_FR)"
InstType "$(INST_TYPE_US)"

;Installer Sections
Section $(SECTION_MAIN) SecMain
	SectionIn 1 2 RO
    ; Ensure that we have VC++ 2015 runtime (for python 3.5)
    Call ensureVCRedist

	; TODO: may be we can automatically rebuild the dlls here.
	; http://stackoverflow.com/questions/24580/how-do-you-automate-a-visual-studio-build
	; For example, we can build the Visual Studio solution with the following command line.
	; C:\Program Files (x86)\Microsoft Visual Studio 12.0\Common7\IDE\devenv.com "..\build\PIME.sln" /build Release

	SetOverwrite on ; overwrite existing files
	SetOutPath "$INSTDIR"

    ; Install version info
    File "..\version.txt"

    ; Install backend informations
    File "..\backends.json"

	; Install the launcher responsible to launch the backends
	File "..\build\PIMELauncher\Release\PIMELauncher.exe"

	SetOutPath "$INSTDIR\python\input_methods"
    File /r "..\python\input_methods\arabic"
    StrCpy $INST_PYTHON "True"
SectionEnd

SectionGroup /e $(PYTHON_SECTION_GROUP) python_section_group
    Section $(FRENCH) french
    	SectionIn 1 RO
    SectionEnd
    Section $(US) us
    	SectionIn 2 RO
    SectionEnd
SectionGroupEnd

Section "" Register
	SectionIn 1 2
	; Install the python backend and input method modules along with an embeddable version of python 3.
	${If} $INST_PYTHON == "True"
		SetOutPath "$INSTDIR"
		File /r /x "__pycache__" /x "input_methods" /x ".git" /x ".idea" "..\python"
		SetOutPath "$INSTDIR\python\input_methods"
		File "..\python\input_methods\__init__.py"
	${EndIf}

	${If} ${SectionIsSelected} ${french}
    		!insertmacro _ReplaceInFile "$INSTDIR\python\input_methods\arabic\ime.json" "%locale" "fr-FR"
    ${EndIf}
    ${If} ${SectionIsSelected} ${us}
        	!insertmacro _ReplaceInFile "$INSTDIR\python\input_methods\arabic\ime.json" "%locale" "en-US"
    ${EndIf}

	; Install the text service dlls
	${If} ${RunningX64} ; This is a 64-bit Windows system
		SetOutPath "$INSTDIR\x64"
		${If} $UPDATEX64DLL == "True"
			File "..\build64\PIMETextService\Release\PIMETextService.dll" ; put 64-bit PIMETextService.dll in x64 folder
		${EndIf}
		; Register COM objects (NSIS RegDLL command is broken and cannot be used)
		ExecWait '"$SYSDIR\regsvr32.exe" /s "$INSTDIR\x64\PIMETextService.dll"'
	${EndIf}
	SetOutPath "$INSTDIR\x86"
	${If} $UPDATEX86DLL == "True"
		File "..\build\PIMETextService\Release\PIMETextService.dll" ; put 32-bit PIMETextService.dll in x86 folder
	${EndIf}
	; Register COM objects (NSIS RegDLL command is broken and cannot be used)
	ExecWait '"$SYSDIR\regsvr32.exe" /s "$INSTDIR\x86\PIMETextService.dll"'

	; Launch the python server on startup
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "PIMELauncher" "$INSTDIR\PIMELauncher.exe"

	;Store installation folder in the registry
	WriteRegStr HKLM "Software\PIME" "" $INSTDIR
	;Write an entry to Add & Remove applications
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" $(PRODUCT_NAME)
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" $(PRODUCT_PUBLISHER)
	; WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\x86\PIMETextService.dll"
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${HOMEPAGE_URL}"
	WriteUninstaller "$INSTDIR\Uninstall.exe" ;Create uninstaller

	; Compile all installed python modules to *.pyc files
	${If} $INST_PYTHON == "True"
		nsExec::ExecToLog  '"$INSTDIR\python\python3\python.exe" -m compileall "$INSTDIR\python"'
	${EndIf}

	; Launch the python server as current user (non-elevated process)
	${StdUtils.ExecShellAsUser} $0 "$INSTDIR\PIMELauncher.exe" "open" ""

	; Custom IE Protected Mode
	ReadINIStr $0 "$PLUGINSDIR\ieprotectedpage.ini" "Field 2" State
	${If} $0 == "1"
		WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" "2500" 0x00000003
	${Else}
		WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" "2500" 0x00000000
	${EndIf}

	; Create shortcuts
	CreateDirectory "$SMPROGRAMS\$(PRODUCT_NAME)"
	CreateShortCut "$SMPROGRAMS\$(PRODUCT_NAME)\$(UNINSTALL_PIME).lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

;Assign language strings to sections
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
	!insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(SecMain_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${python_section_group} $(PYTHON_SECTION_GROUP_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${french} $(french_DESC)
    !insertmacro MUI_DESCRIPTION_TEXT ${us} $(us_DESC)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;Uninstaller Section
Section "Uninstall"
	; Remove the launcher from auto-start
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PIME"
	DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "PIMELauncher"
	DeleteRegKey /ifempty HKLM "Software\PIME"

	; Unregister COM objects (NSIS UnRegDLL command is broken and cannot be used)
	ExecWait '"$SYSDIR\regsvr32.exe" /u /s "$INSTDIR\x86\PIMETextService.dll"'
	${If} ${RunningX64}
		SetRegView 64 ; disable registry redirection and use 64 bit Windows registry directly
		ExecWait '"$SYSDIR\regsvr32.exe" /u /s "$INSTDIR\x64\PIMETextService.dll"'
		RMDir /REBOOTOK /r "$INSTDIR\x64"
	${EndIf}

	; Try to terminate running PIMELauncher and the server process
	; Otherwise we cannot replace it.
	ExecWait '"$INSTDIR\PIMELauncher.exe" /quit'
	Delete /REBOOTOK "$INSTDIR\PIMELauncher.exe"

	RMDir /REBOOTOK /r "$INSTDIR\x86"
	RMDir /REBOOTOK /r "$INSTDIR\python"
    Delete "$INSTDIR\backends.json"

	; Delete shortcuts
	Delete "$SMPROGRAMS\$(PRODUCT_NAME)\$(UNINSTALL_PIME).lnk"
	RMDir "$SMPROGRAMS\$(PRODUCT_NAME)"

	Delete "$INSTDIR\version.txt"
	Delete "$INSTDIR\Uninstall.exe"
	RMDir "$INSTDIR"

	${If} ${RebootFlag}
		MessageBox MB_YESNO "$(MB_REBOOT_REQUIRED)" IDNO +3
		Reboot
		Quit
		Abort
	${EndIf}
SectionEnd
