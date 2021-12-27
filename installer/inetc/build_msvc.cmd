@echo off
setlocal
set Name=INetC
set DistRoot=.
set SrcRoot=%DistRoot%\Contrib\%Name%
set BaseCL=/GL /LD /W3 /O1 /Osy /GF /Gz /GS- /GR- /Zl /D_VC_NODEFAULTLIB
set BaseLINK=/LTCG /DLL /OPT:REF /OPT:ICF,99 /MERGE:.rdata=.text /OPT:NOWIN98 /NODEFAULTLIB kernel32.lib user32.lib advapi32.lib comctl32.lib wininet.lib
set Targets=x86-ansi x86-unicode
(>nul (( 2>&1 call cl "/?" )|find /I "AMD64"))&&(set Targets=amd64-unicode)
for %%A in (%Targets%) do (call :B %%A)
@goto :EOF


:B targ
set DEF=/D___NSISPLUGIN
((echo %1|find /I "unicode")>nul)&&set DEF=%DEF% /DUNICODE /D_UNICODE
set CL=%BaseCL% %DEF% /Gy
set LINK=%BaseLINK%
for %%B in (%SrcRoot%\*.rc) do call RC /R /FO"%DistRoot%\%%~nB.res" "%%B"
for %%A in (c cpp cxx) do for %%B in (%SrcRoot%\*.%%A) do (
	if exist "%DistRoot%\%%~nB.obj" del "%DistRoot%\%%~nB.obj"
	call CL /c %%B /Fe"%DistRoot%\%Name%"
	)
md "%DistRoot%\Plugins\%1" 2>nul
call LINK /NOLOGO /OUT:"%DistRoot%\Plugins\%1\%Name%.dll" /PDB:"%DistRoot%\%Name%-%1" "%DistRoot%\*.obj" "%DistRoot%\*.res"
@goto :EOF
