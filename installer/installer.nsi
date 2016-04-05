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

Unicode true ; turn on Unicode (This requires NSIS 3.0)
SetCompressor /SOLID lzma ; use LZMA for best compression ratio
SetCompressorDictSize 16 ; larger dictionary size for better compression ratio
AllowSkipFiles off ; cannot skip a file

; icons of the generated installer and uninstaller
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall.ico"

!define PRODUCT_NAME "PIME 輸入法"
!define /file PRODUCT_VERSION "..\version.txt"

!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\PIME"
!define HOMEPAGE_URL "https://github.com/EasyIME/"

!define chewing_value "0404:{35F67E9D-A54D-4177-9697-8B0AB71A9E04}{F80736AA-28DB-423A-92C9-5540F501C939}"
!define newcj_value "0404:{35F67E9D-A54D-4177-9697-8B0AB71A9E04}{D5F17DA0-594A-5897-9B0C-9BA79F000000}"
!define checj_value "0404:{35F67E9D-A54D-4177-9697-8B0AB71A9E04}{F828D2DC-81BE-466E-9CFE-24BB03172693}"

Name "${PRODUCT_NAME}"
BrandingText "${PRODUCT_NAME}"

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
!insertmacro MUI_PAGE_COMPONENTS

; installation progress page
!insertmacro MUI_PAGE_INSTFILES

; finish page
!define MUI_FINISHPAGE_LINK_LOCATION "${HOMEPAGE_URL}"
!define MUI_FINISHPAGE_LINK "PIME 專案網頁 ${MUI_FINISHPAGE_LINK_LOCATION}"
!insertmacro MUI_PAGE_FINISH

; uninstallation pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
;--------------------------------

!insertmacro MUI_LANGUAGE "TradChinese" ; traditional Chinese

; Uninstall old versions
Function uninstallOldVersion
	ClearErrors
	;  run uninstaller
	ReadRegStr $R0 HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
	${If} $R0 != ""
		ClearErrors
        ${If} ${FileExists} "$INSTDIR\Uninstall.exe"
            MessageBox MB_OKCANCEL|MB_ICONQUESTION "偵測到已安裝舊版，是否要移除舊版後繼續安裝新版？" IDOK +2
                Abort ; this is skipped if the user select OK

            CopyFiles "$INSTDIR\Uninstall.exe" "$TEMP"
            ExecWait '"$TEMP\Uninstall.exe" _?=$INSTDIR'
            Delete "$TEMP\Uninstall.exe"
        ${EndIf}
	${EndIf}

	ClearErrors
	; Ensure that old files are all deleted
	${If} ${RunningX64}
		${If} ${FileExists} "$INSTDIR\x64\PIMETextService.dll"
            Delete /REBOOTOK "$INSTDIR\x64\PIMETextService.dll"
            IfErrors 0 +2
                Call .onInstFailed
		${EndIf}
	${EndIf}
	${If} ${FileExists} "$INSTDIR\x86\PIMETextService.dll"
        Delete /REBOOTOK "$INSTDIR\x86\PIMETextService.dll"
        IfErrors 0 +2
            Call .onInstFailed
	${EndIf}

	${If} ${RebootFlag}
		Call .onInstFailed
	${EndIf}
FunctionEnd

; Called during installer initialization
Function .onInit
	; Currently, we're not able to support Windows xp since it has an incomplete TSF.
	${IfNot} ${AtLeastWinVista}
		MessageBox MB_ICONSTOP|MB_OK "抱歉，本程式目前只能支援 Windows Vista 以上版本"
		Quit
	${EndIf}

	${If} ${RunningX64} 
		SetRegView 64 ; disable registry redirection and use 64 bit Windows registry directly
	${EndIf}

	; check if old version is installed and uninstall it first
	Call uninstallOldVersion

FunctionEnd

; called to show an error message when errors happen
Function .onInstFailed
	${If} ${RebootFlag}
		MessageBox MB_YESNO "安裝發生錯誤，無法完成。$\r$\n有時是有檔案正在使用中，暫時無法刪除或覆寫。$\n$\n建議重新開機後，再次執行安裝程式。$\r$\n你要立即重新開機嗎？ (若你想要在稍後才重新開機請選擇「否」)" IDNO +2
		Reboot
		Abort
	${Else}
		MessageBox MB_ICONSTOP|MB_OK "安裝發生錯誤，無法完成。$\n$\n有時是有檔案正在使用中，暫時無法刪除或覆寫。$\n$\n建議重新開機後，再次執行安裝程式。"
		Abort
	${EndIf}
FunctionEnd

Function ensureVCRedist
    ; Check if we have Universal CRT (provided by VC++ 2015 runtime)
    ; Reference: https://blogs.msdn.microsoft.com/vcblog/2015/03/03/introducing-the-universal-crt/
    ;            https://docs.python.org/3/using/windows.html#embedded-distribution
    ${IfNot} ${FileExists} "$SYSDIR\ucrtbase.dll"
        MessageBox MB_YESNO|MB_ICONQUESTION "這個程式需要微軟 VC++ 2015 runtime 更新才能運作，要自動下載安裝？" IDYES +2
            Abort ; this is skipped if the user select Yes
        ; Download VC++ 2015 redistibutable (x86 version)
        nsisdl::download "http://download.microsoft.com/download/9/3/F/93FCF1E7-E6A4-478B-96E7-D4B285925B00/vc_redist.x86.exe" "$TEMP\vc2015_redist.x86.exe"
        Pop $R0 ;Get the return value
        ${If} $R0 != "success"
            MessageBox MB_ICONSTOP|MB_OK "無法正確下載，請稍後再試，或手動安裝 VC++ 2015 runtime (x86)"
            Abort
        ${EndIf}

        ; Run vcredist installer
        ExecWait "$TEMP\vc2015_redist.x86.exe" $0

        ; check again is ucrtbase.dll is available
        ${IfNot} ${FileExists} "$SYSDIR\ucrtbase.dll"
            MessageBox MB_ICONSTOP|MB_OK "VC++ 2015 runtime (x86) 並未正確安裝，請參閱相關微軟文件進行更新。"
            ExecShell "open" "https://support.microsoft.com/en-us/kb/2999226"
            Abort
        ${EndIf}
    ${EndIf}

	; Check if we have VC++ 2013 runtime (required by OpenCC library)
	${IfNot} ${FileExists} "$SYSDIR\msvcr120.dll"
        MessageBox MB_YESNO|MB_ICONQUESTION "這個程式需要微軟 VC++ 2013 runtime 才能運作，要自動下載安裝？" IDYES +2
            Abort ; this is skipped if the user select Yes
        ; Download VC++ 2013 redistibutable (x86 version)
        nsisdl::download "https://download.microsoft.com/download/8/1/6/816C537F-BE60-4341-883B-84D143D0AE96/vcredist_x86.exe" "$TEMP\vc2013_redist.x86.exe"
        Pop $R0 ;Get the return value
        ${If} $R0 != "success"
            MessageBox MB_ICONSTOP|MB_OK "無法正確下載，請稍後再試，或手動安裝 VC++ 2015 runtime (x86)"
            Abort
        ${EndIf}

        ; Run vcredist installer
        ExecWait "$TEMP\vc2013_redist.x86.exe" $0

        ; check again is msvcr120.dll is available
        ${IfNot} ${FileExists} "$SYSDIR\msvcr120.dll"
            MessageBox MB_ICONSTOP|MB_OK "VC++ 2013 runtime (x86) 並未正確安裝，請參閱相關微軟文件進行更新。"
            ExecShell "open" "https://www.microsoft.com/zh-TW/download/details.aspx?id=40784"
            Abort
        ${EndIf}
	${EndIf}
FunctionEnd

;Installer Type
InstType "$(INST_TYPE_STD)"
InstType "$(INST_TYPE_FULL)"

;Installer Sections
Section "PIME 輸入法平台" SecMain
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

    ; Install an embedable version of python 3.
    File /r "..\python"
    
	; Install the python server and input method modules
    ; FIXME: maybe we should install the pyc files later?
	File /r /x "__pycache__" /x "meow" /x "chewing" /x "newcj" /x "checj" "..\server"

    ; Install the launcher and monitor of the server
	File "..\build\PIMELauncher\Release\PIMELauncher.exe"
SectionEnd

SubSection "輸入法模組"
	Section "新酷音" chewing
		SectionIn 1 2
		SetOutPath "$INSTDIR\server\input_methods"
		File /r "..\server\input_methods\chewing"
	SectionEnd

	Section "自由大新倉頡" newcj
		SectionIn 2
		SetOutPath "$INSTDIR\server\input_methods"
		File /r "..\server\input_methods\newcj"
	SectionEnd

	Section "酷倉" checj
		SectionIn 2
		SetOutPath "$INSTDIR\server\input_methods"
		File /r "..\server\input_methods\checj"
	SectionEnd
SubSectionEnd

Section "" Register
	SectionIn 1 2
	; Install the text service dlls
	${If} ${RunningX64} ; This is a 64-bit Windows system
		SetOutPath "$INSTDIR\x64"
		File "..\build64\pime\Release\PIMETextService.dll" ; put 64-bit PIMETextService.dll in x64 folder
		; Register COM objects (NSIS RegDLL command is broken and cannot be used)
		ExecWait '"$SYSDIR\regsvr32.exe" /s "$INSTDIR\x64\PIMETextService.dll"'
	${EndIf}
	SetOutPath "$INSTDIR\x86"
	File "..\build\pime\Release\PIMETextService.dll" ; put 32-bit PIMETextService.dll in x86 folder
	; Register COM objects (NSIS RegDLL command is broken and cannot be used)
	ExecWait '"$SYSDIR\regsvr32.exe" /s "$INSTDIR\x86\PIMETextService.dll"'

	; Launch the python server on startup
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "PIMELauncher" "$INSTDIR\PIMELauncher.exe"

	;Store installation folder in the registry
	WriteRegStr HKLM "Software\PIME" "" $INSTDIR
	;Write an entry to Add & Remove applications
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "PIME 輸入法"
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "PIME 開發團隊"
	; WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\x86\PIMETextService.dll"
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${HOMEPAGE_URL}"
	WriteUninstaller "$INSTDIR\Uninstall.exe" ;Create uninstaller

	; Compile all installed python modules to *.pyc files
	nsExec::ExecToLog  '"$INSTDIR\python\python.exe" -m compileall "$INSTDIR\server"'

	; Launch the python server as current user (non-elevated process)
	${StdUtils.ExecShellAsUser} $0 "$INSTDIR\PIMELauncher.exe" "open" ""

	${If} ${AtLeastWin8}
		StrCpy $R0 0
		StrCpy $0 0
		loop:
			EnumRegValue $1 HKCU "Control Panel\International\User Profile\zh-Hant-TW" $0
			StrCmp $1 "" done
			IntOp $0 $0 + 1
			${If} $1 ==  ${chewing_value}
			${OrIf} $1 == ${newcj_value}
			${OrIf} $1 == ${checj_value}
				IntOp $R0 $R0 + 0
			${Else}
				IntOp $R0 $R0 + 1
			${EndIf}
			Goto loop
		done:

		${If} ${SectionIsSelected} ${chewing}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" ${chewing_value} $R0
		${EndIf}

		${If} ${SectionIsSelected} ${newcj}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" ${newcj_value} $R0
		${EndIf}

		${If} ${SectionIsSelected} ${checj}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" ${checj_value} $R0
		${EndIf}
	${EndIf}

	; Create shortcuts
	CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
	${If} ${SectionIsSelected} ${chewing}
		CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\設定新酷音輸入法.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\server\input_methods\chewing\config\configTool.py"' "$INSTDIR\server\input_methods\chewing\icon.ico" 0
	${EndIf}
	
	${If} ${SectionIsSelected} ${checj}
		CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\設定酷倉輸入法.lnk" "$INSTDIR\server\input_methods\checj\config\config.hta" "" "$INSTDIR\server\input_methods\checj\icon.ico" 0
	${EndIf}
	CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\解除安裝 PIME.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

;Language strings
LangString DESC_SecMain ${LANG_ENGLISH} "A test section." ; What's this??
LangString INST_TYPE_STD ${CHT} "標準安裝"
LangString INST_TYPE_FULL ${CHT} "完整安裝"
LangString MB_REBOOT_REQUIRED ${CHT} "安裝程式需要重新開機來完成解除安裝。$\r$\n你要立即重新開機嗎？ (若你想要在稍後才重新開機請選擇「否」)"

;Assign language strings to sections
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
	!insertmacro MUI_DESCRIPTION_TEXT ${SecMain} "安裝 ${PRODUCT_NAME} 主程式到你的電腦裏。"
	!insertmacro MUI_DESCRIPTION_TEXT ${chewing} "安裝新酷音輸入法模組。"
	!insertmacro MUI_DESCRIPTION_TEXT ${newcj} "安裝自由大新倉頡輸入法模組。"
	!insertmacro MUI_DESCRIPTION_TEXT ${checj} "安裝酷倉輸入法模組。"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;Uninstaller Section
Section "Uninstall"
    ; Remove the launcher from auto-start
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PIME"
	DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "PIMELauncher"
	DeleteRegKey /ifempty HKLM "Software\PIME"

	${If} ${AtLeastWin8}
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" ${chewing_value}
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW"  ${newcj_value}
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW"  ${checj_value}
	${EndIf}

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
	RMDir /REBOOTOK /r "$INSTDIR\server"
	RMDir /REBOOTOK /r "$INSTDIR\python"

    ; Delete shortcuts
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定新酷音輸入法.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定酷倉輸入法.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME}\解除安裝 PIME.lnk"
    RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

	Delete "$INSTDIR\version.txt"
	Delete "$INSTDIR\Uninstall.exe"
	RMDir "$INSTDIR"

	${If} ${RebootFlag}
		MessageBox MB_YESNO "$(MB_REBOOT_REQUIRED)" IDNO +2
		Reboot
	${EndIf}
SectionEnd

