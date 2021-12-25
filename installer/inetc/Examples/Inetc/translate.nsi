
;--------------------------------
; General Attributes

Name "Inetc Translate Test"
OutFile "Translate.exe"
RequestExecutionLevel user


;--------------------------------
;Interface Settings

  !include "MUI2.nsh"
  !define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install-colorful.ico"
  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH
  !insertmacro MUI_LANGUAGE "Russian"


;--------------------------------
;Installer Sections

Section "Dummy Section" SecDummy

; This is russian variant. See Readme.txt for a list of parameters.
; Use LangStrings as TRANSLATE parameters for multilang options

    inetc::load /POPUP "" /CAPTION "���� �������" /TRANSLATE "URL" "��������" "������� ����������" "��� �����" �������� "������" "��������" "������" "http://ineum.narod.ru/g06s.htm" "$EXEDIR\g06s.htm"
    Pop $0 # return value = exit code, "OK" if OK
    MessageBox MB_OK "Download Status: $0"

SectionEnd
