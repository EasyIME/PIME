/**************************************************************
 ***  Generates a md5 value from a file, string or random.  ***
 **************************************************************/

Name "MD5dll Example"
OutFile "MD5dllTest.exe"
ShowInstDetails show

Section 
	# generate MD5sum of file
	StrCpy $0 "${NSISDIR}\NSIS.CHM"
	md5dll::GetMD5File "$0"
	Pop $1

	DetailPrint 'md5dll::GetMD5File "$0"'
	DetailPrint "MD5: [$1]"
	DetailPrint ""

	# generate MD5sum of file using deprecated method
	StrCpy $0 "${NSISDIR}\NSIS.CHM"
	md5dll::GetFileMD5 "$0"
	Pop $1

	DetailPrint '{deprecated} md5dll::GetFileMD5 "$0"'
	DetailPrint "MD5: [$1]"
	DetailPrint ""


	#generate MD5sum of string
	StrCpy $0 "MyString"
	md5dll::GetMD5String "$0"
	Pop $1

	DetailPrint 'md5dll::GetMD5String "$0"'
	DetailPrint "MD5: [$1]"
	DetailPrint ""

	#generate MD5sum of string using deprecated method
	StrCpy $0 "MyString"
	md5dll::GetMD5 "$0"
	Pop $1

	DetailPrint '{deprecated} md5dll::GetMD5 "$0"'
	DetailPrint "MD5: [$1]"
	DetailPrint ""


	#generate random MD5sum
	md5dll::GetMD5Random
	Pop $1

	DetailPrint "md5dll::GetMD5Random"
	DetailPrint "MD5: [$1]"
	DetailPrint ""
SectionEnd
