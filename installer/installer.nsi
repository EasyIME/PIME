;
;	Copyright (C) 2013 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

Unicode true ; turn on Unicode (This requires NSIS 3.0)
SetCompressor lzma ; use LZMA for best compression ratio
AllowSkipFiles off ; cannot skip a file

; icons of the generated installer and uninstaller
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall.ico"
!define PRODUCT_VERSION "git"

!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChewingTextService"

Name "新酷音輸入法"
BrandingText "新酷音輸入法"

OutFile "windows-chewing-tsf.exe" ; The generated installer file name

; We install everything to C:\Program Files (x86)
InstallDir "$PROGRAMFILES32\ChewingTextService"

;Request application privileges (need administrator to install)
RequestExecutionLevel admin
!define MUI_ABORTWARNING

;Pages
; license page
!insertmacro MUI_PAGE_LICENSE "..\COPYING.txt"

; !insertmacro MUI_PAGE_COMPONENTS

; installation progress page
!insertmacro MUI_PAGE_INSTFILES

; finish page
!define MUI_FINISHPAGE_LINK_LOCATION "http://chewing.im/"
!define MUI_FINISHPAGE_LINK "新酷音專案網頁 ${MUI_FINISHPAGE_LINK_LOCATION}"
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
		MessageBox MB_OKCANCEL|MB_ICONQUESTION "偵測到已安裝舊版，是否要移除舊版後繼續安裝新版？" IDOK +2
			Abort ; this is skipped if the user select OK

		CopyFiles "$INSTDIR\Uninstall.exe" "$TEMP"
		ExecWait '"$TEMP\Uninstall.exe" _?=$INSTDIR'
		Delete "$TEMP\Uninstall.exe"
	${EndIf}

	;ClearErrors
	; Ensure that old files are all deleted
	;${If} ${RunningX64}
	;	${If} ${FileExists} "$INSTDIR\x64\ChewingTextService.dll"
	;		Call onInstError
	;	${EndIf}			
	;${EndIf}
	;${If} ${FileExists} "$INSTDIR\x86\ChewingTextService.dll"
	;	Call onInstError
	;${EndIf}			
	;${If} ${FileExists} "$INSTDIR\Dictionary\*.dat"
	;	Call onInstError
	;${EndIf}
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
	MessageBox MB_ICONSTOP|MB_OK "安裝發生錯誤，無法完成。$\n$\n可能有檔案正在使用中，暫時無法刪除或覆寫$\n$\n建議重新開機後，再次執行安裝程式。"
FunctionEnd

; called to show an error message when errors happen
;Function onInstError
;	MessageBox MB_ICONSTOP|MB_OK "安裝發生錯誤，舊版可能有檔案正在使用中，暫時無法覆寫$\n$\n請重開機後，再次執行安裝程式。"
;	Abort
;FunctionEnd

;Installer Sections
Section "新酷音輸入法" SecMain
	SetOutPath "$INSTDIR"
	SetOverwrite on ; overwrite existing files
	${If} ${RunningX64}
		File /r "x64" ; put 64-bit ChewingTextService.dll in x64 folder
	${EndIf}
	File /r "x86" ; put 32-bit ChewingTextService.dll in x86 folder
	File /r Dictionary ; Install dictionary files
	File ChewingPreferences.exe ; Configuration Tool

	; Register COM objects (NSIS RegDLL command is broken and cannot be used)
	ExecWait '"$SYSDIR\regsvr32.exe" /s "$INSTDIR\x86\ChewingTextService.dll"'
	${If} ${RunningX64} 
		ExecWait '"$SYSDIR\regsvr32.exe" /s "$INSTDIR\x64\ChewingTextService.dll"'
	${EndIf}

	; Special handling for Windows 8
	${If} ${AtLeastWin8}
		File SetupChewing.bat
		${If} ${RunningX64}
			WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "SetupChewing" \
				"rundll32.exe $\"$INSTDIR\x64\ChewingTextService.dll$\",ChewingSetup"
		${Else}
			WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "SetupChewing" \
				"rundll32.exe $\"$INSTDIR\x86\ChewingTextService.dll$\",ChewingSetup"
		${EndIf}
		; Run SetupChewing.bat as current user (ask explorer to open it for us)
		; Reference: http:;mdb-blog.blogspot.tw/2013/01/nsis-lunch-program-as-user-from-uac.html
		; Though it's more reliable to use the UAC plugin, I think this hack is enough for most cases.
		ExecWait 'explorer.exe "$INSTDIR\SetupChewing.bat"'
	${EndIf}

	;Store installation folder in the registry
	WriteRegStr HKLM "Software\ChewingTextService" "" $INSTDIR
	;Write an entry to Add & Remove applications
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "新酷音輸入法 (TSF)"
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "新酷音輸入法開發團隊"
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\x86\ChewingTextService.dll"
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
	WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "http://chewing.im/"
	WriteUninstaller "$INSTDIR\Uninstall.exe" ;Create uninstaller
SectionEnd

;Language strings
LangString DESC_SecMain ${LANG_ENGLISH} "A test section." ; What's this??

;Assign language strings to sections
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;Uninstaller Section
Section "Uninstall"

	; Unregister COM objects (NSIS UnRegDLL command is broken and cannot be used)
	ExecWait '"$SYSDIR\regsvr32.exe" /u /s "$INSTDIR\x86\ChewingTextService.dll"'
	${If} ${RunningX64} 
		SetRegView 64 ; disable registry redirection and use 64 bit Windows registry directly
		ExecWait '"$SYSDIR\regsvr32.exe" /u /s "$INSTDIR\x64\ChewingTextService.dll"'
		RMDir /r "$INSTDIR\x64"
	${EndIf}

	RMDir /r "$INSTDIR\x86"
	RMDir /r "$INSTDIR\Dictionary"
	Delete "$INSTDIR\SetupChewing.bat"
	Delete "$INSTDIR\ChewingPreferences.exe"

	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChewingTextService"
	DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "SetupChewing"
	DeleteRegKey /ifempty HKLM "Software\ChewingTextService"

	Delete "$INSTDIR\Uninstall.exe"
	RMDir "$INSTDIR"

SectionEnd

