﻿;
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

; icons of the generated installer and uninstaller
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall.ico"

!define PRODUCT_NAME "PIME 輸入法"
!define /file PRODUCT_VERSION "..\version.txt"

!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\PIME"
!define HOMEPAGE_URL "https://github.com/EasyIME/"

!define PIME_CLSID "{35F67E9D-A54D-4177-9697-8B0AB71A9E04}"

!define CHEWING_GUID "{F80736AA-28DB-423A-92C9-5540F501C939}"
!define CHECJ_GUID "{F828D2DC-81BE-466E-9CFE-24BB03172693}"
; !define CHELIU_GUID "{72844B94-5908-4674-8626-4353755BC5DB}"
!define CHEARRAY_GUID "{BADFF6B6-0502-4F30-AEC2-BCCB92BCDDC6}"
!define CHEDAYI_GUID "{E6943374-70F5-4540-AA0F-3205C7DCCA84}"
!define CHEPINYIN_GUID "{945765E9-9898-477B-B282-856FC3BA907E}"
!define CHESIMPLEX_GUID "{C7E3DA59-A9D8-4A3B-90DC-58700FAF20CD}"
!define EMOJIME_GUID "{A381D463-9338-4FBD-B83D-66FFB03523B3}"
!define CHEENG_GUID "{88BB09A8-4603-4D78-B052-DEE9EAE697EC}"


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

; Custom IE Protected Mode
; custom page
Var HWND
ReserveFile ".\resource\ieprotectedpage.ini"
Page custom setIEProtectedPage leaveIEProtectedPage

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

var UPDATEX86DLL
var UPDATEX64DLL

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

			; Remove the launcher from auto-start
			DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PIME"
			DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "PIMELauncher"
			DeleteRegKey /ifempty HKLM "Software\PIME"

			${If} ${AtLeastWin8}
				DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEWING_GUID}"
				DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHECJ_GUID}"
				; DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHELIU_GUID}"
				DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEARRAY_GUID}"
				DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEDAYI_GUID}"
				DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEPINYIN_GUID}"
				DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHESIMPLEX_GUID}"
				DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${EMOJIME_GUID}"
				DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEENG_GUID}"
			${EndIf}

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
			Delete /REBOOTOK "$INSTDIR\libpipe.dll"
			Delete "$INSTDIR\profile_backends.cache"

			RMDir /REBOOTOK /r "$INSTDIR\python"
			RMDir /REBOOTOK /r "$INSTDIR\node"

			; Delete shortcuts
			Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定新酷音輸入法.lnk"
			Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定酷倉輸入法.lnk"
			Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定蝦米輸入法.lnk"
			Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定行列輸入法.lnk"
			Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定大易輸入法.lnk"
			Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定拼音輸入法.lnk"
			Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定速成輸入法.lnk"
			Delete "$SMPROGRAMS\${PRODUCT_NAME}\解除安裝 PIME.lnk"
			RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

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
	; Currently, we're not able to support Windows xp since it has an incomplete TSF.
	${IfNot} ${AtLeastWinVista}
		MessageBox MB_ICONSTOP|MB_OK "抱歉，本程式目前只能支援 Windows Vista 以上版本"
		Quit
	${EndIf}

	${If} ${RunningX64}
		SetRegView 64 ; disable registry redirection and use 64 bit Windows registry directly
	${EndIf}

	InitPluginsDir
	File "/oname=$PLUGINSDIR\ieprotectedpage.ini" ".\resource\ieprotectedpage.ini"
	File "/oname=$PLUGINSDIR\PIMETextService_x86.dll" "..\build\pime\Release\PIMETextService.dll"
	File "/oname=$PLUGINSDIR\PIMETextService_x64.dll" "..\build64\pime\Release\PIMETextService.dll"

	StrCpy $UPDATEX86DLL "True"
	StrCpy $UPDATEX64DLL "True"

	; check if old version is installed and uninstall it first
	Call uninstallOldVersion
	Call hideCheEngSection
FunctionEnd

; called to show an error message when errors happen
Function .onInstFailed
	${If} ${RebootFlag}
		MessageBox MB_YESNO "安裝發生錯誤，無法完成。$\r$\n有時是有檔案正在使用中，暫時無法刪除或覆寫。$\n$\n建議重新開機後，再次執行安裝程式。$\r$\n你要立即重新開機嗎？ (若你想要在稍後才重新開機請選擇「否」)" IDNO +3
		Reboot
		Quit
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

; Custom IE Protected Mode
Function setIEProtectedPage
	ReadRegDWORD $R0 HKCU "Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" "2500"
	${If} $R0 == 3
		WriteINIStr "$PLUGINSDIR\ieprotectedpage.ini" "Field 2" State 1
	${Endif}
	InstallOptions::initDialog /NOUNLOAD "$PLUGINSDIR\ieprotectedpage.ini"
	Pop $HWND
	!insertmacro MUI_HEADER_TEXT "變更 IE 設定" "PIME 輸入法須要變更 IE 設定，才能在 IE 裡使用。"

	GetDlgItem $0 $HWND 1205
	EnableWindow $0 0
	InstallOptions::show
FunctionEnd

; Custom IE Protected Mode
Function leaveIEProtectedPage
	ReadINIStr $0 "$PLUGINSDIR\ieprotectedpage.ini" Settings State
	${Switch} $0
		${Default}
			Abort
		${Case} 2
			GetDlgItem $1 $HWND 1205
			EnableWindow $1 0
			Abort
		${Case} 0
	${EndSwitch}
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

    ; Install the libpipe dll.
    File "..\build\libpipe\Release\libpipe.dll"

	; Install the python backend and input method modules along with an embedable version of python 3.
	File /r /x "__pycache__" /x "input_methods" /x ".git" /x ".idea" "..\python"
	SetOutPath "$INSTDIR\python\input_methods"
	File "..\python\input_methods\__init__.py"

	SetOutPath "$INSTDIR"
	; Install the node.js backend and input method modules along with an embedable version of node v6.
	File /r /x "input_methods" "..\node"

	; Install the launcher responsible to launch the backends
	File "..\build\PIMELauncher\Release\PIMELauncher.exe"
SectionEnd

SectionGroup /e "輸入法模組"
	Section "新酷音" chewing
		SectionIn 1 2
		SetOutPath "$INSTDIR\python\input_methods"
		File /r "..\python\input_methods\chewing"
	SectionEnd

	Section "酷倉" checj
		SectionIn 2
		SetOutPath "$INSTDIR\python\input_methods"
		File /r "..\python\input_methods\checj"
	SectionEnd
/*
	Section "蝦米" cheliu
		SectionIn 2
		SetOutPath "$INSTDIR\python\input_methods"
		File /r "..\python\input_methods\cheliu"
	SectionEnd
*/
	Section "行列" chearray
		SectionIn 2
		SetOutPath "$INSTDIR\python\input_methods"
		File /r "..\python\input_methods\chearray"
	SectionEnd

	Section "大易" chedayi
		SectionIn 2
		SetOutPath "$INSTDIR\python\input_methods"
		File /r "..\python\input_methods\chedayi"
	SectionEnd

	Section "拼音" chepinyin
		SectionIn 2
		SetOutPath "$INSTDIR\python\input_methods"
		File /r "..\python\input_methods\chepinyin"
	SectionEnd

	Section "速成" chesimplex
		SectionIn 2
		SetOutPath "$INSTDIR\python\input_methods"
		File /r "..\python\input_methods\chesimplex"
	SectionEnd

	Section "emojime" emojime
			SectionIn 2
			SetOutPath "$INSTDIR\node\input_methods"
			File /r "..\node\input_methods\emojime"
	SectionEnd

	Section /o "英數" cheeng
		${If} ${AtLeastWin8}
			SectionIn 2
			SetOutPath "$INSTDIR\python\input_methods"
			File /r "..\python\input_methods\cheeng"
		${EndIf}
	SectionEnd
SectionGroupEnd

Function hideCheEngSection
	${IfNot} ${AtLeastWin8}
		SectionSetText ${cheeng} ""
	${EndIf}
FunctionEnd

Section "" Register
	SectionIn 1 2
	; Install the text service dlls
	${If} ${RunningX64} ; This is a 64-bit Windows system
		SetOutPath "$INSTDIR\x64"
		${If} $UPDATEX64DLL == "True"
			File "..\build64\pime\Release\PIMETextService.dll" ; put 64-bit PIMETextService.dll in x64 folder
		${EndIf}
		; Register COM objects (NSIS RegDLL command is broken and cannot be used)
		ExecWait '"$SYSDIR\regsvr32.exe" /s "$INSTDIR\x64\PIMETextService.dll"'
	${EndIf}
	SetOutPath "$INSTDIR\x86"
	${If} $UPDATEX86DLL == "True"
		File "..\build\pime\Release\PIMETextService.dll" ; put 32-bit PIMETextService.dll in x86 folder
	${EndIf}
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
	nsExec::ExecToLog  '"$INSTDIR\python\python.exe" -m compileall "$INSTDIR\python"'

	; Launch the python server as current user (non-elevated process)
	${StdUtils.ExecShellAsUser} $0 "$INSTDIR\PIMELauncher.exe" "open" ""

	${If} ${AtLeastWin8}
		StrCpy $R0 0
		StrCpy $0 0
		loop:
			EnumRegValue $1 HKCU "Control Panel\International\User Profile\zh-Hant-TW" $0
			StrCmp $1 "" done
			IntOp $0 $0 + 1
			IntOp $R0 $R0 + 1
			Goto loop
		done:

		${If} ${SectionIsSelected} ${chewing}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEWING_GUID}" $R0
		${EndIf}

		${If} ${SectionIsSelected} ${checj}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHECJ_GUID}" $R0
		${EndIf}
/*
		${If} ${SectionIsSelected} ${cheliu}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHELIU_GUID}" $R0
		${EndIf}
*/
		${If} ${SectionIsSelected} ${chearray}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEARRAY_GUID}" $R0
		${EndIf}

		${If} ${SectionIsSelected} ${chedayi}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEDAYI_GUID}" $R0
		${EndIf}

		${If} ${SectionIsSelected} ${chepinyin}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEPINYIN_GUID}" $R0
		${EndIf}

		${If} ${SectionIsSelected} ${chesimplex}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHESIMPLEX_GUID}" $R0
		${EndIf}

		${If} ${SectionIsSelected} ${emojime}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${EMOJIME_GUID}" $R0
		${EndIf}

		${If} ${SectionIsSelected} ${cheeng}
			IntOp $R0 $R0 + 1
			WriteRegDWORD HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEENG_GUID}" $R0
		${EndIf}
	${EndIf}

	; Custom IE Protected Mode
	ReadINIStr $0 "$PLUGINSDIR\ieprotectedpage.ini" "Field 2" State
	${If} $0 == "1"
		WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" "2500" 0x00000003
	${Else}
		WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones\3" "2500" 0x00000000
	${EndIf}

	; Create shortcuts
	CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
	${If} ${SectionIsSelected} ${chewing}
		CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\設定新酷音輸入法.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\python\input_methods\chewing\config\configTool.py"' "$INSTDIR\python\input_methods\chewing\icon.ico" 0
	${EndIf}

	${If} ${SectionIsSelected} ${checj}
		CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\設定酷倉輸入法.lnk" "$INSTDIR\python\input_methods\checj\config\config.hta" "" "$INSTDIR\python\input_methods\checj\icon.ico" 0
	${EndIf}
/*
	${If} ${SectionIsSelected} ${cheliu}
		CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\設定蝦米輸入法.lnk" "$INSTDIR\python\input_methods\cheliu\config\config.hta" "" "$INSTDIR\python\input_methods\cheliu\icon.ico" 0
	${EndIf}
*/
	${If} ${SectionIsSelected} ${chearray}
		CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\設定行列輸入法.lnk" "$INSTDIR\python\input_methods\chearray\config\config.hta" "" "$INSTDIR\python\input_methods\chearray\icon.ico" 0
	${EndIf}

	${If} ${SectionIsSelected} ${chedayi}
		CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\設定大易輸入法.lnk" "$INSTDIR\python\input_methods\chedayi\config\config.hta" "" "$INSTDIR\python\input_methods\chedayi\icon.ico" 0
	${EndIf}

	${If} ${SectionIsSelected} ${chepinyin}
		CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\設定拼音輸入法.lnk" "$INSTDIR\python\input_methods\chepinyin\config\config.hta" "" "$INSTDIR\python\input_methods\chepinyin\icon.ico" 0
	${EndIf}

	${If} ${SectionIsSelected} ${chesimplex}
		CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\設定速成輸入法.lnk" "$INSTDIR\python\input_methods\chesimplex\config\config.hta" "" "$INSTDIR\python\input_methods\chesimplex\icon.ico" 0
	${EndIf}

	CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\解除安裝 PIME.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

;Language strings
!define CHT 1028
LangString INST_TYPE_STD ${CHT} "標準安裝"
LangString INST_TYPE_FULL ${CHT} "完整安裝"
LangString MB_REBOOT_REQUIRED ${CHT} "安裝程式需要重新開機來完成解除安裝。$\r$\n你要立即重新開機嗎？ (若你想要在稍後才重新開機請選擇「否」)"

;Assign language strings to sections
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
	!insertmacro MUI_DESCRIPTION_TEXT ${SecMain} "安裝 ${PRODUCT_NAME} 主程式到你的電腦裏。"
	!insertmacro MUI_DESCRIPTION_TEXT ${chewing} "安裝新酷音輸入法模組。"
	!insertmacro MUI_DESCRIPTION_TEXT ${checj} "安裝酷倉輸入法模組。"
	; !insertmacro MUI_DESCRIPTION_TEXT ${cheliu} "安裝蝦米輸入法模組。"
	!insertmacro MUI_DESCRIPTION_TEXT ${chearray} "安裝行列輸入法模組。"
	!insertmacro MUI_DESCRIPTION_TEXT ${chedayi} "安裝大易輸入法模組。"
	!insertmacro MUI_DESCRIPTION_TEXT ${chepinyin} "安裝拼音輸入法模組。"
	!insertmacro MUI_DESCRIPTION_TEXT ${chesimplex} "安裝速成輸入法模組。"
	!insertmacro MUI_DESCRIPTION_TEXT ${emojime} "安裝 emojime 輸入法模組。"
	!insertmacro MUI_DESCRIPTION_TEXT ${cheeng} "安裝英數輸入法模組。"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;Uninstaller Section
Section "Uninstall"
	; Remove the launcher from auto-start
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PIME"
	DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "PIMELauncher"
	DeleteRegKey /ifempty HKLM "Software\PIME"

	${If} ${AtLeastWin8}
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEWING_GUID}"
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHECJ_GUID}"
		; DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHELIU_GUID}"
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEARRAY_GUID}"
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEDAYI_GUID}"
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEPINYIN_GUID}"
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHESIMPLEX_GUID}"
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${EMOJIME_GUID}"
		DeleteRegValue HKCU "Control Panel\International\User Profile\zh-Hant-TW" "0404:${PIME_CLSID}${CHEENG_GUID}"
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
	Delete /REBOOTOK "$INSTDIR\libpipe.dll"
	Delete "$INSTDIR\profile_backends.cache"

	RMDir /REBOOTOK /r "$INSTDIR\x86"
	RMDir /REBOOTOK /r "$INSTDIR\python"
	RMDir /REBOOTOK /r "$INSTDIR\node"

	; Delete shortcuts
	Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定新酷音輸入法.lnk"
	Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定酷倉輸入法.lnk"
	Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定蝦米輸入法.lnk"
	Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定行列輸入法.lnk"
	Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定大易輸入法.lnk"
	Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定拼音輸入法.lnk"
	Delete "$SMPROGRAMS\${PRODUCT_NAME}\設定速成輸入法.lnk"
	Delete "$SMPROGRAMS\${PRODUCT_NAME}\解除安裝 PIME.lnk"
	RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

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
