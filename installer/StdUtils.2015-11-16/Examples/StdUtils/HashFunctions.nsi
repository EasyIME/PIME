Caption "StdUtils Test-Suite"

!addincludedir  "..\..\Include"

!ifdef NSIS_UNICODE
	!addplugindir "..\..\Plugins\Release_Unicode"
	OutFile "HashFunctions-Unicode.exe"
!else
	!addplugindir "..\..\Plugins\Release_ANSI"
	OutFile "HashFunctions-ANSI.exe"
!endif

!include 'StdUtils.nsh'

RequestExecutionLevel user
ShowInstDetails show

!define TestData "The quick brown fox jumps over the lazy dog"
!define TestFile "$WINDIR\Explorer.exe"

!macro _MyHashText type text
	${StdUtils.HashText} $0 "${type}" "${text}"
	DetailPrint '${type}("${text}") = $0'
!macroend
!define MyHashText "!insertmacro _MyHashText"

!macro _MyHashFile type file
	${StdUtils.HashFile} $0 "${type}" "${file}"
	DetailPrint '${type}(${file}) = $0'
!macroend
!define MyHashFile "!insertmacro _MyHashFile"

Section
	${MyHashText} "CRC-32"     ""
	${MyHashText} "MD5-128"    ""
	${MyHashText} "SHA1-160"   ""
	${MyHashText} "SHA2-224"   ""
	${MyHashText} "SHA2-256"   ""
	${MyHashText} "SHA2-384"   ""
	${MyHashText} "SHA2-512"   ""
	${MyHashText} "SHA3-224"   ""
	${MyHashText} "SHA3-256"   ""
	${MyHashText} "SHA3-384"   ""
	${MyHashText} "SHA3-512"   ""
	${MyHashText} "BLAKE2-224" ""
	${MyHashText} "BLAKE2-256" ""
	${MyHashText} "BLAKE2-384" ""
	${MyHashText} "BLAKE2-512" ""
	DetailPrint "----"
SectionEnd

Section
	${MyHashText} "CRC-32"     "${TestData}"
	${MyHashText} "MD5-128"    "${TestData}"
	${MyHashText} "SHA1-160"   "${TestData}"
	${MyHashText} "SHA1-160"   "${TestData}"
	${MyHashText} "SHA2-224"   "${TestData}"
	${MyHashText} "SHA2-256"   "${TestData}"
	${MyHashText} "SHA2-384"   "${TestData}"
	${MyHashText} "SHA2-512"   "${TestData}"
	${MyHashText} "SHA3-224"   "${TestData}"
	${MyHashText} "SHA3-256"   "${TestData}"
	${MyHashText} "SHA3-384"   "${TestData}"
	${MyHashText} "SHA3-512"   "${TestData}"
	${MyHashText} "BLAKE2-224" "${TestData}"
	${MyHashText} "BLAKE2-256" "${TestData}"
	${MyHashText} "BLAKE2-384" "${TestData}"
	${MyHashText} "BLAKE2-512" "${TestData}"
	DetailPrint "----"
SectionEnd

Section
	${MyHashFile} "CRC-32"     "${TestFile}"
	${MyHashFile} "MD5-128"    "${TestFile}"
	${MyHashFile} "SHA1-160"   "${TestFile}"
	${MyHashFile} "SHA1-160"   "${TestFile}"
	${MyHashFile} "SHA2-224"   "${TestFile}"
	${MyHashFile} "SHA2-256"   "${TestFile}"
	${MyHashFile} "SHA2-384"   "${TestFile}"
	${MyHashFile} "SHA2-512"   "${TestFile}"
	${MyHashFile} "SHA3-224"   "${TestFile}"
	${MyHashFile} "SHA3-256"   "${TestFile}"
	${MyHashFile} "SHA3-384"   "${TestFile}"
	${MyHashFile} "SHA3-512"   "${TestFile}"
	${MyHashFile} "BLAKE2-224" "${TestFile}"
	${MyHashFile} "BLAKE2-256" "${TestFile}"
	${MyHashFile} "BLAKE2-384" "${TestFile}"
	${MyHashFile} "BLAKE2-512" "${TestFile}"

	DetailPrint "----"
SectionEnd
