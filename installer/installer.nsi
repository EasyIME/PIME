; NOTE: This file MUST be saved as UTF-8 with BOM (utf-8-sig) so that
; NSIS (makensis) natively detects Unicode strings without breaking Git diffs.
; Do NOT convert this file to UTF-16.
; AI-assisted change (#966): Codex (GPT-6) removed the obsolete VC++ Redistributable check.
;
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

!include "macros.nsh"

Unicode true ; turn on Unicode (This requires NSIS 3.0)
SetCompressor /SOLID lzma ; use LZMA for best compression ratio
SetCompressorDictSize 16 ; larger dictionary size for better compression ratio
AllowSkipFiles off ; cannot skip a file

; icons of the generated installer and uninstaller
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall.ico"

!define /file PRODUCT_VERSION "..\version.txt"

!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\PIME"
!define HOMEPAGE_URL "https://github.com/EasyIME/"

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
!define MUI_FINISHPAGE_LINK_LOCATION "${HOMEPAGE_URL}"
!define MUI_FINISHPAGE_LINK "$(PRODUCT_PAGE) ${MUI_FINISHPAGE_LINK_LOCATION}"
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

!insertmacro LANG_LOAD "TradChinese" ; Traditional Chinese
!insertmacro LANG_LOAD "SimpChinese" ; Simplified Chinese
!insertmacro LANG_LOAD "English" ; English

var INST_PYTHON
var INST_CINBASE
var INST_NODE

; The table file of Liu input method
var LIU_UNI_TAB_FILE

; Uninstall old versions
Function uninstallOldVersion
	ClearErrors
	;  run uninstaller
	ReadRegStr $R0 HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
	${If} $R0 != ""
		ClearErrors
		${If} ${FileExists} "$INSTDIR\Uninstall.exe"
			MessageBox MB_OKCANCEL|MB_ICONQUESTION $(UNINSTALL_OLD) /SD IDOK IDOK +2
			Abort ; this is skipped if the user select OK

			; Ask running PIMELauncher to quit gracefully
			!insertmacro StopPIMELauncher

			; Unregister COM objects (NSIS UnRegDLL command is broken and cannot be used)
			!insertmacro UnregisterTextService 32 "$INSTDIR\x86\PIMETextService.dll"
			${If} ${IsNativeAMD64}
				!insertmacro UnregisterTextService 64 "$INSTDIR\x64\PIMETextService.dll"
			${ElseIf} ${IsNativeARM64}
				!insertmacro UnregisterTextService 64 "$INSTDIR\arm64\PIMETextService.dll"
			${EndIf}

			; Remove the launcher from auto-start and clean registry
			!insertmacro CleanPIMERegistry

			; Safely remove or rename old binaries so the destination paths are free for writing.
			; If files are locked by running applications, SafeDeleteFile renames them to unique
			; temporary files scheduled for deletion on reboot without blocking immediate installation.
			!insertmacro CleanOldBinaries

			; Clean old backend and data files
			Delete "$INSTDIR\backends.json"
			RMDir /r "$INSTDIR\python"
			RMDir /r "$INSTDIR\node"

			; Only exist in earlier versions, but need to delete it.
			RMDir /r "$INSTDIR\server"

			; Delete shortcuts in Start Menu
			RMDir /r "$SMPROGRAMS\$(PRODUCT_NAME)"

			Delete "$INSTDIR\version.txt"
			Delete "$INSTDIR\Uninstall.exe"

			${If} ${RebootFlag}
				Call .onInstFailed
			${EndIf}
		${EndIf}
	${EndIf}
FunctionEnd

; Called during installer initialization
Function .onInit
	;Language selection dialog

	${IfNot} ${Silent}
		Push ""
		Push ${LANG_TRADCHINESE}
		Push "繁體中文"
		Push ${LANG_SIMPCHINESE}
		Push "简体中文"
		Push ${LANG_ENGLISH}
		Push "English"
		Push A ; A means auto count languages
			   ; for the auto count to work the first empty push (Push "") must remain
		LangDLL::LangDialog $(INSTALLER_LANGUAGE_TITLE) $(INSTALL_LANGUAGE_MESSAGE)

		Pop $LANGUAGE
		StrCmp $LANGUAGE "cancel" 0 +2
			Abort
	${EndIf}

	; Currently, we're not able to support Windows xp since it has an incomplete TSF.
	${IfNot} ${AtLeastWinVista}
		MessageBox MB_ICONSTOP|MB_OK $(AtLeastWinVista_MESSAGE)
		Quit
	${EndIf}

	; The installer is an x86 (32-bit) binary. On 64-bit Windows (x64 and ARM64),
	; the WOW64 subsystem automatically redirects all registry writes to WOW6432Node.
	; Enable 64-bit registry view globally so NSIS registry commands (WriteRegStr,
	; ReadRegStr, DeleteRegKey) target native 64-bit keys (HKLM\Software\PIME, Run,
	; and Uninstall\PIME), allowing 64-bit apps and the OS uninstaller to find PIME.
	${If} ${RunningX64}
	${OrIf} ${IsNativeARM64}
		SetRegView 64
	${EndIf}

	; Check if an earlier uninstallation or update scheduled locked files or directories
	; to be deleted on reboot. If so, reinstalling before rebooting will cause Windows
	; Session Manager to wipe the newly installed files on the next restart.
	!insertmacro CheckPendingFileRename "$INSTDIR" $R0
	${If} $R0 == "True"
		MessageBox MB_YESNO|MB_ICONEXCLAMATION $(PENDING_REBOOT_QUESTION) /SD IDYES IDYES +2
		Quit
		Reboot
	${EndIf}



	StrCpy $INST_PYTHON "False"
	StrCpy $INST_CINBASE "False"
	StrCpy $INST_NODE "False"

	; check if old version is installed and uninstall it first
	Call uninstallOldVersion
	Call hideSection
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

;Installer Type
InstType "$(INST_TYPE_STD)"
InstType "$(INST_TYPE_FULL)"

;Installer Sections
Section $(SECTION_MAIN) SecMain
	SectionIn 1 2 RO
	SetOverwrite on ; overwrite existing files
	SetOutPath "$INSTDIR"

    ; Install version info
    File "..\version.txt"

    ; Install backend informations
    File "..\backends.json"

	; Safely clean/rename old binaries before writing new ones
	!insertmacro CleanOldBinaries

	; Install the launcher responsible to launch the backends
	File "..\build\PIMELauncher\PIMELauncher.exe"
SectionEnd

SectionGroup /e $(PYTHON_SECTION_GROUP) python_section_group
	SectionGroup /e $(PYTHON_CHT_SECTION_GROUP) python_cht_section_group
		Section $(CHEWING) chewing
			SectionIn 1 2
			SetOutPath "$INSTDIR\python\input_methods\chewing"
			File /r "..\python\input_methods\chewing\*.*"
			StrCpy $INST_PYTHON "True"
		SectionEnd

		Section $(CHECJ) checj
			SectionIn 2
			SetOutPath "$INSTDIR\python\input_methods\checj"
			File /r "..\python\input_methods\checj\*.*"
			StrCpy $INST_PYTHON "True"
			StrCpy $INST_CINBASE "True"
		SectionEnd

		Section $(CHELIU) cheliu
            SectionIn 2
            ; Ask the user to provide "liu-uni.tab" file
            MessageBox MB_OK|MB_ICONQUESTION "$(SELECT_LIU_FILE)"
            nsDialogs::SelectFileDialog open "" "liu-uni.tab file|liu-uni.tab"
            Pop $LIU_UNI_TAB_FILE
			${If} ${FileExists} "$LIU_UNI_TAB_FILE"
				SetOutPath "$INSTDIR\python\input_methods\cheliu"
				File /r "..\python\input_methods\cheliu\*.*"
				SetOutPath "$INSTDIR\python\cinbase\cin"
				StrCpy $INST_PYTHON "True"
				StrCpy $INST_CINBASE "True"
            ${Else}
                MessageBox MB_OK|MB_ICONSTOP "$(CANNOT_INSTALL_LIU)"
                StrCpy $LIU_UNI_TAB_FILE ""
			${EndIf}
		SectionEnd

		Section $(CHEARRAY) chearray
			SectionIn 2
			SetOutPath "$INSTDIR\python\input_methods\chearray"
			File /r "..\python\input_methods\chearray\*.*"
			StrCpy $INST_PYTHON "True"
			StrCpy $INST_CINBASE "True"
		SectionEnd

		Section $(CHEDAYI) chedayi
			SectionIn 2
			SetOutPath "$INSTDIR\python\input_methods\chedayi"
			File /r "..\python\input_methods\chedayi\*.*"
			StrCpy $INST_PYTHON "True"
			StrCpy $INST_CINBASE "True"
		SectionEnd

		Section $(CHEPINYIN) chepinyin
			SectionIn 2
			SetOutPath "$INSTDIR\python\input_methods\chepinyin"
			File /r "..\python\input_methods\chepinyin\*.*"
			StrCpy $INST_PYTHON "True"
			StrCpy $INST_CINBASE "True"
		SectionEnd

		Section $(CHESIMPLEX) chesimplex
			SectionIn 2
			SetOutPath "$INSTDIR\python\input_methods\chesimplex"
			File /r "..\python\input_methods\chesimplex\*.*"
			StrCpy $INST_PYTHON "True"
			StrCpy $INST_CINBASE "True"
		SectionEnd

		Section $(CHEPHONETIC) chephonetic
			SectionIn 2
			SetOutPath "$INSTDIR\python\input_methods\chephonetic"
			File /r "..\python\input_methods\chephonetic\*.*"
			StrCpy $INST_PYTHON "True"
			StrCpy $INST_CINBASE "True"
		SectionEnd

		Section $(CHEEZ) cheez
			SectionIn 2
			SetOutPath "$INSTDIR\python\input_methods\cheez"
			File /r "..\python\input_methods\cheez\*.*"
			StrCpy $INST_PYTHON "True"
			StrCpy $INST_CINBASE "True"
		SectionEnd

		Section $(CHEENG) cheeng
			${If} ${AtLeastWin8}
				SectionIn 2
				SetOutPath "$INSTDIR\python\input_methods\cheeng"
				File /r "..\python\input_methods\cheeng\*.*"
				StrCpy $INST_PYTHON "True"
			${EndIf}
		SectionEnd

		Section $(BRAILLE_CHEWING) braille_chewing
            SectionIn 2
            SetOutPath "$INSTDIR\python\input_methods\braille_chewing"
            File /r "..\python\input_methods\braille_chewing\*.*"
            StrCpy $INST_PYTHON "True"
		SectionEnd

    SectionGroupEnd

	SectionGroup /e $(PYTHON_CHS_SECTION_GROUP) python_chs_section_group
		Section $(RIME) rime
			SectionIn 2
			SetOutPath "$INSTDIR\python\input_methods\rime"
			File /r /x "brise" "..\python\input_methods\rime\*.*"
			SetOutPath "$INSTDIR\python\input_methods\rime\data"
			File "..\python\input_methods\rime\brise\*.txt"
			File "..\python\input_methods\rime\brise\*.yaml"
			File "..\python\input_methods\rime\brise\preset\*.yaml"
			File "..\python\input_methods\rime\brise\supplement\*.yaml"
			File "..\python\input_methods\rime\brise\extra\*.yaml"
			SetOutPath "$INSTDIR\python\input_methods\rime\data\opencc"
			File "..\python\opencc\*.json" "..\python\opencc\*.ocd"
			StrCpy $INST_PYTHON "True"
		SectionEnd
	SectionGroupEnd
SectionGroupEnd

SectionGroup /e $(NODE_SECTION_GROUP) node_section_group
	SectionGroup /e $(NODE_CHT_SECTION_GROUP) node_cht_section_group
		Section $(MCBOPOMOFO) McBopomofo
				SectionIn 2
				SetOutPath "$INSTDIR\node\input_methods\McBopomofo"
				File /r /x "server.js" /x "webpack_check.js" /x "run_*.bat" /x "README.md" /x "*.txt" "..\node\input_methods\McBopomofo\*.*"
				StrCpy $INST_NODE "True"
		SectionEnd

		Section $(MCFOXIM) McFoxim
				SectionIn 2
				SetOutPath "$INSTDIR\node\input_methods\McFoxim"
				File /r /x "server.js" /x "webpack_check.js" /x "run_*.bat" /x "README.md" /x "*.txt" "..\node\input_methods\McFoxim\*.*"
				StrCpy $INST_NODE "True"
		SectionEnd

		Section $(MCTABIM) McTabim
				SectionIn 2
				SetOutPath "$INSTDIR\node\input_methods\McTabim"
				File /r /x "server.js" /x "webpack_check.js" /x "run_*.bat" /x "README.md" /x "*.txt" "..\node\input_methods\McTabim\*.*"
				StrCpy $INST_NODE "True"
		SectionEnd

		Section $(EMOJIME) emojime
				SectionIn 2
				SetOutPath "$INSTDIR\node\input_methods\emojime"
				File /oname=index.js "..\node\input_methods\emojime\dist\index.js"
				File "..\node\input_methods\emojime\ime.json"
				File "..\node\input_methods\emojime\icon.ico"
				StrCpy $INST_NODE "True"
		SectionEnd
	SectionGroupEnd
SectionGroupEnd

Function hideSection
	${IfNot} ${AtLeastWin8}
		SectionSetText ${cheeng} ""
	${EndIf}
FunctionEnd

Section "" Register
	SectionIn 1 2
	; Install the python backend and input method modules along with an embedable version of python 3.
	${If} $INST_PYTHON == "True"
		SetOutPath "$INSTDIR\python"
		File /r /x "__pycache__" /x "input_methods" /x "cinbase" /x ".git" /x ".idea" "..\python\*.*"
		SetOutPath "$INSTDIR\python\input_methods"
		File "..\python\input_methods\__init__.py"
	${EndIf}

	; Install the CinBase Class for all cin-based input method modules.
	${If} $INST_CINBASE == "True"
		SetOutPath "$INSTDIR\python"
		File /r /x "__pycache__" /x "cin" "..\python\cinbase"
        ${If} ${SectionIsSelected} ${cheliu}
            ; Convert the tab file to *.cin format first.
            nsExec::ExecToLog '"$INSTDIR\python\python3\python.exe" "$INSTDIR\python\cinbase\tools\liu_unitab2cin.py" "$LIU_UNI_TAB_FILE" "$INSTDIR\python\cinbase\cin\liu.cin"'
            ; Convert the liu.cin file to json format used by cinbase.
            nsExec::ExecToLog '"$INSTDIR\python\python3\python.exe" "$INSTDIR\python\cinbase\tools\cintojson.py" "liu.cin"'
        ${EndIf}
	${EndIf}

	; Install the node.js backend and input method modules along with an embedable version of node v6.
	${If} $INST_NODE == "True"
		SetOutPath "$INSTDIR\node"
		File /r /x "input_methods" "..\node\*.*"
	${EndIf}

	; Install the text service dlls
	${If} ${IsNativeAMD64} ; This is a 64-bit x86-64/x64 Windows system
		SetOutPath "$INSTDIR\x64"
		File "..\build64\PIMETextService\Release\PIMETextService.dll"
		!insertmacro RegisterTextService 64 "$INSTDIR\x64\PIMETextService.dll"
	${ElseIf} ${IsNativeARM64} ; This is a native ARM64 Windows system
		SetOutPath "$INSTDIR\arm64"
		; ARM64X forwarder DLL (built in build_arm64\PIMETextService\Release\PIMETextService.dll)
		File "..\build_arm64\PIMETextService\Release\PIMETextService.dll"
		; Real native ARM64 DLL (built in build_arm64\PIMETextService\Release\PIMETextService_arm64.dll)
		File "..\build_arm64\PIMETextService\Release\PIMETextService_arm64.dll"
		; Real x64 DLL for emulated x64 / ARM64EC processes (built in build64\PIMETextService\Release\PIMETextService.dll)
		File "/oname=PIMETextService_x64.dll" "..\build64\PIMETextService\Release\PIMETextService.dll"
		; Register COM objects (only register the ARM64X forwarder DLL)
		!insertmacro RegisterTextService 64 "$INSTDIR\arm64\PIMETextService.dll"
	${EndIf}

	SetOutPath "$INSTDIR\x86"
	File "..\build\PIMETextService\Release\PIMETextService.dll"
	!insertmacro RegisterTextService 32 "$INSTDIR\x86\PIMETextService.dll"

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

	; Create shortcuts
	CreateDirectory "$SMPROGRAMS\$(PRODUCT_NAME)"
	${If} ${SectionIsSelected} ${chewing}
		CreateShortCut "$SMPROGRAMS\$(PRODUCT_NAME)\$(SET_CHEWING).lnk" "$INSTDIR\python\python3\pythonw.exe" '"$INSTDIR\python\input_methods\chewing\config_tool.py" config' "$INSTDIR\python\input_methods\chewing\images\setting.ico" 0
		CreateShortCut "$SMPROGRAMS\$(PRODUCT_NAME)\$(SET_CHEWING_PHRASES).lnk" "$INSTDIR\python\python3\pythonw.exe" '"$INSTDIR\python\input_methods\chewing\config_tool.py" user_phrase_editor' "$INSTDIR\python\input_methods\chewing\images\phrase_editor.ico" 0
	${EndIf}

	!insertmacro CreateCinBaseShortcut ${checj} $(SET_CHECJ) checj
	!insertmacro CreateCinBaseShortcut ${cheliu} $(SET_CHELIU) cheliu
	!insertmacro CreateCinBaseShortcut ${chearray} $(SET_CHEARRAY) chearray
	!insertmacro CreateCinBaseShortcut ${chedayi} $(SET_CHEDAYI) chedayi
	!insertmacro CreateCinBaseShortcut ${chepinyin} $(SET_CHEPINYIN) chepinyin
	!insertmacro CreateCinBaseShortcut ${chesimplex} $(SET_CHESIMPLEX) chesimplex
	!insertmacro CreateCinBaseShortcut ${chephonetic} $(SET_CHEPHONETIC) chephonetic
	!insertmacro CreateCinBaseShortcut ${cheez} $(SET_CHEEZ) cheez

	CreateShortCut "$SMPROGRAMS\$(PRODUCT_NAME)\$(UNINSTALL_PIME).lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

;Assign language strings to sections
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
	!insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(SecMain_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${python_section_group} $(PYTHON_SECTION_GROUP_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${python_cht_section_group} $(PYTHON_CHT_SECTION_GROUP_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${python_chs_section_group} $(PYTHON_CHS_SECTION_GROUP_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${node_section_group} $(NODE_SECTION_GROUP_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${node_cht_section_group} $(NODE_CHT_SECTION_GROUP_DESC)
	;!insertmacro MUI_DESCRIPTION_TEXT ${node_chs_section_group} $(NODE_CHS_SECTION_GROUP_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${chewing} $(chewing_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${checj} $(checj_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${cheliu} $(cheliu_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${chearray} $(chearray_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${chedayi} $(chedayi_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${chepinyin} $(chepinyin_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${chesimplex} $(chesimplex_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${chephonetic} $(chephonetic_DESC)
    !insertmacro MUI_DESCRIPTION_TEXT ${cheez} $(cheez_DESC)
    !insertmacro MUI_DESCRIPTION_TEXT ${rime} $(rime_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${mcbopomofo} $(mcbopomofo_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${mcfoxim} $(mcfoxim_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${mctabim} $(mctabim_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${emojime} $(emojime_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${cheeng} $(cheeng_DESC)
	!insertmacro MUI_DESCRIPTION_TEXT ${braille_chewing} $(braille_chewing_DESC)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;Uninstaller Section
Section "Uninstall"
	${If} ${RunningX64}
	${OrIf} ${IsNativeARM64}
		SetRegView 64 ; Disable WOW64 registry redirection on 64-bit systems
	${EndIf}

	; Try to terminate running PIMELauncher and the server process
	!insertmacro StopPIMELauncher
	; Unregister COM objects (NSIS UnRegDLL command is broken and cannot be used)
	!insertmacro UnregisterTextService 32 "$INSTDIR\x86\PIMETextService.dll"
	${If} ${IsNativeAMD64}
		!insertmacro UnregisterTextService 64 "$INSTDIR\x64\PIMETextService.dll"
	${ElseIf} ${IsNativeARM64}
		!insertmacro UnregisterTextService 64 "$INSTDIR\arm64\PIMETextService.dll"
	${EndIf}

	; Remove auto-start, uninstall, and product keys from registry
	!insertmacro CleanPIMERegistry

	; Safely delete binaries (which may be locked by running processes)
	!insertmacro CleanOldBinaries
	RMDir /REBOOTOK "$INSTDIR\x86"

	${If} ${IsNativeAMD64}
		RMDir /REBOOTOK "$INSTDIR\x64"
	${ElseIf} ${IsNativeARM64}
		RMDir /REBOOTOK "$INSTDIR\arm64"
	${EndIf}

	RMDir /REBOOTOK /r "$INSTDIR\python"
	RMDir /REBOOTOK /r "$INSTDIR\node"
	Delete "$INSTDIR\backends.json"

	; Delete shortcuts in Start Menu
	RMDir /r "$SMPROGRAMS\$(PRODUCT_NAME)"

	Delete "$INSTDIR\version.txt"
	Delete "$INSTDIR\Uninstall.exe"
	RMDir /REBOOTOK "$INSTDIR"

	${If} ${RebootFlag}
		MessageBox MB_YESNO "$(MB_REBOOT_REQUIRED)" /SD IDNO IDNO +3
		Reboot
		Quit
		Abort
	${EndIf}
SectionEnd
