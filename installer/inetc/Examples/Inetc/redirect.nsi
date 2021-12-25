
;--------------------------------
; General Attributes

Name "Redirect Test"
OutFile "redirect.exe"
RequestExecutionLevel user


;--------------------------------
;Interface Settings

  !include "MUI2.nsh"
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_LANGUAGE "English"


;--------------------------------
;Installer Sections

Section "Dummy Section" SecDummy

    SetDetailsView hide

    inetc::get "http://localhost/redirect.php" "$EXEDIR\redirect.htm" /end
    Pop $1

    MessageBox MB_OK "Download Status: $1"

SectionEnd

