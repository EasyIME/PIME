
;--------------------------------
; General Attributes

Name "Inetc To Stack Test"
OutFile "ToStack.exe"
RequestExecutionLevel user


;--------------------------------
;Interface Settings

  !include "MUI2.nsh"
  !define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install-colorful.ico"
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_LANGUAGE "English"


;--------------------------------
;Installer Sections

Section "Dummy Section" SecDummy

    inetc::get /TOSTACK "http://www.google.com" "" /END
    Pop $0 # return value = exit code, "OK" if OK
    MessageBox MB_OK "Download Status: $0"
    Pop $0 # return text
    StrLen $1 $0
    MessageBox MB_OK "Download Length: $1"
    MessageBox MB_OK "$0"

SectionEnd
