@echo off
setlocal
cd /d "%~dp0"

set "BASE_DIR=PIME_Core\bin\x86\Release"
set "MSI_EN=%BASE_DIR%\en-US\PIME_Core.msi"
set "MSI_TW=%BASE_DIR%\zh-TW\PIME_Core.msi"
set "MSI_CN=%BASE_DIR%\zh-CN\PIME_Core.msi"
set "OUT_DIR=bin"
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"
set "MSI_OUT=%OUT_DIR%\PIME_Core_Multilingual.msi"

if not exist "%MSI_EN%" (
    echo Error: %MSI_EN% not found. Build the WiX project first.
    exit /b 1
)
if not exist "%MSI_TW%" (
    echo Error: %MSI_TW% not found. Build the WiX project first.
    exit /b 1
)
if not exist "%MSI_CN%" (
    echo Error: %MSI_CN% not found. Build the WiX project first.
    exit /b 1
)

set "WSCRIPT_DIR="
for /d %%D in ("%ProgramFiles(x86)%\Windows Kits\10\bin\10.*") do (
    if exist "%%D\x64\wisubstg.vbs" (
        set "WSCRIPT_DIR=%%D\x64"
    ) else if exist "%%D\x86\wisubstg.vbs" (
        set "WSCRIPT_DIR=%%D\x86"
    )
)

if "%WSCRIPT_DIR%"=="" (
    echo Error: Could not locate Windows SDK scripts wisubstg.vbs.
    exit /b 1
)

echo Generating transforms with language validation flags...
wix msi transform "%MSI_EN%" "%MSI_TW%" -t language -out zh-TW.mst
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
wix msi transform "%MSI_EN%" "%MSI_CN%" -t language -out zh-CN.mst
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo Copying base MSI...
copy /y "%MSI_EN%" "%MSI_OUT%" >nul
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo Embedding transforms...
cscript //nologo "%WSCRIPT_DIR%\wisubstg.vbs" "%MSI_OUT%" zh-TW.mst 1028
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
cscript //nologo "%WSCRIPT_DIR%\wisubstg.vbs" "%MSI_OUT%" zh-TW.mst 3076
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
cscript //nologo "%WSCRIPT_DIR%\wisubstg.vbs" "%MSI_OUT%" zh-TW.mst 5124
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
cscript //nologo "%WSCRIPT_DIR%\wisubstg.vbs" "%MSI_OUT%" zh-CN.mst 2052
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
cscript //nologo "%WSCRIPT_DIR%\wisubstg.vbs" "%MSI_OUT%" zh-CN.mst 4100
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo Updating Summary Information languages...
cscript //nologo "%WSCRIPT_DIR%\wilangid.vbs" "%MSI_OUT%" Package 1033,1028,2052,3076,5124,4100
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo Cleaning up intermediate files...
if exist zh-TW.mst del zh-TW.mst
if exist zh-CN.mst del zh-CN.mst

copy /y "%MSI_OUT%" PIME_Core_Multilingual.msi >nul

echo Done! Output is %MSI_OUT%
endlocal
