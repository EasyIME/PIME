@echo off
setlocal

echo ============================================
echo  PIME Go Backend Build Script
echo ============================================
echo.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
for %%I in ("%ROOT_DIR%\..") do set "PIME_ROOT=%%~fI"
set "BUILD_ROOT=%ROOT_DIR%\build"
set "PACKAGE_DIR=%BUILD_ROOT%\go-backend"
set "SERVER_EXE=%PACKAGE_DIR%\server.exe"
set "BACKEND_SNIPPET=%BUILD_ROOT%\backends.go-backend.json"
set "RIME_DIR=%ROOT_DIR%\input_methods\rime"
set "RIME_DATA_DIR=%RIME_DIR%\data"
set "PACKAGE_RIME_DIR=%PACKAGE_DIR%\input_methods\rime"
set "PACKAGE_RIME_DATA_DIR=%PACKAGE_RIME_DIR%\data"
set "PLUM_DIR=%PIME_ROOT%\plum"
set "PLUM_INSTALL=%PLUM_DIR%\rime-install"
set "PLUM_INSTALL_BAT=%PLUM_DIR%\rime-install.bat"
set "PLUM_PRESET_TARGET=:preset"
set "WEASEL_ROOT="
set "WEASEL_DATA_DIR="

REM Check Go environment
where go >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Go was not found in PATH.
    echo Install Go from: https://golang.org/dl/
    exit /b 1
)

for /f "tokens=3" %%i in ('go version') do (
    echo [INFO] Go version: %%i
)

echo.
echo ============================================
echo Step 1: Prepare output directory
echo ============================================
echo.

if exist "%PACKAGE_DIR%" (
    echo [INFO] Removing old build output: "%PACKAGE_DIR%"
    rmdir /s /q "%PACKAGE_DIR%"
)

mkdir "%PACKAGE_DIR%"
if errorlevel 1 (
    echo [ERROR] Failed to create output directory: "%PACKAGE_DIR%"
    exit /b 1
)

echo [INFO] Output directory: "%PACKAGE_DIR%"

if not exist "%RIME_DATA_DIR%\default.yaml" (
    echo [ERROR] Missing Go Rime shared data: "%RIME_DATA_DIR%"
    echo [ERROR] Initialize the submodule from https://github.com/gaboolic/rime-frost
    exit /b 1
)

echo.
echo ============================================
echo Step 2: Sync Go dependencies
echo ============================================
echo.

pushd "%ROOT_DIR%"
go mod tidy
if errorlevel 1 (
    echo [WARN] go mod tidy failed, continuing...
)

echo.
echo ============================================
echo Step 3: Build go-backend server
echo ============================================
echo.

set "GOOS=windows"
set "GOARCH=amd64"
set "CGO_ENABLED=0"

echo [INFO] Building server.exe with dynamic DLL loading ...
go build -ldflags "-s -w" -o "%SERVER_EXE%" .
if errorlevel 1 (
    echo [ERROR] Failed to build server.exe
    popd
    exit /b 1
)

echo [INFO] Built: "%SERVER_EXE%"

echo.
echo ============================================
echo Step 4: Copy input_methods
echo ============================================
echo.

if not exist "%ROOT_DIR%\input_methods" (
    echo [ERROR] Missing input_methods directory: "%ROOT_DIR%\input_methods"
    popd
    exit /b 1
)

xcopy "%ROOT_DIR%\input_methods" "%PACKAGE_DIR%\input_methods\" /E /I /Y >nul
if errorlevel 1 (
    echo [ERROR] Failed to copy input_methods
    popd
    exit /b 1
)

echo [INFO] input_methods copied

echo.
echo ============================================
echo Step 5: Prepare packaged Rime shared data
echo ============================================
echo.

call :prepare_rime_data
if errorlevel 1 (
    echo [ERROR] Failed to prepare packaged Rime shared data
    popd
    exit /b 1
)

if exist "%PACKAGE_DIR%\input_methods\rime\brise" (
    rmdir /s /q "%PACKAGE_DIR%\input_methods\rime\brise"
    if errorlevel 1 (
        echo [ERROR] Failed to remove packaged rime\brise directory
        popd
        exit /b 1
    )
    echo [INFO] Removed rime\brise from package output
)

if exist "%PACKAGE_DIR%\input_methods\rime\*.go" (
    del /q "%PACKAGE_DIR%\input_methods\rime\*.go" >nul
    if errorlevel 1 (
        echo [ERROR] Failed to remove packaged Go source files
        popd
        exit /b 1
    )
    echo [INFO] Removed packaged Go source files
)

if exist "%PACKAGE_DIR%\input_methods\rime\rime.dll.bak-32bit" (
    del /q "%PACKAGE_DIR%\input_methods\rime\rime.dll.bak-32bit" >nul
    if errorlevel 1 (
        echo [ERROR] Failed to remove packaged backup DLL
        popd
        exit /b 1
    )
    echo [INFO] Removed packaged backup DLL
)

if exist "%PACKAGE_DIR%\input_methods\rime\icons\icons" (
    rmdir /s /q "%PACKAGE_DIR%\input_methods\rime\icons\icons"
    if errorlevel 1 (
        echo [ERROR] Failed to remove nested icons directory
        popd
        exit /b 1
    )
    echo [INFO] Removed nested icons directory
)

if exist "%RIME_DIR%\rime.dll" (
    copy /Y "%RIME_DIR%\rime.dll" "%PACKAGE_DIR%\input_methods\rime\rime.dll" >nul
    echo [INFO] Copied rime.dll into package output
)

echo.
echo ============================================
echo Step 6: Generate backends.json snippet
echo ============================================
echo.

> "%BACKEND_SNIPPET%" echo [
>> "%BACKEND_SNIPPET%" echo   {
>> "%BACKEND_SNIPPET%" echo     "name": "go-backend",
>> "%BACKEND_SNIPPET%" echo     "command": "go-backend\\server.exe",
>> "%BACKEND_SNIPPET%" echo     "workingDir": "go-backend",
>> "%BACKEND_SNIPPET%" echo     "params": ""
>> "%BACKEND_SNIPPET%" echo   }
>> "%BACKEND_SNIPPET%" echo ]

echo [INFO] Generated: "%BACKEND_SNIPPET%"
popd

echo.
echo ============================================
echo Build completed
echo ============================================
echo.
echo Output directory:
echo   "%PACKAGE_DIR%"
echo.
echo Install target:
echo   C:\Program Files (x86)\PIME\go-backend
echo.
echo Notes:
echo 1. backends.json in this repo uses a top-level array.
echo 2. Ensure C:\Program Files (x86)\PIME\backends.json includes go-backend.
echo 3. Ensure C:\Program Files (x86)\PIME\go-backend\input_methods\*\ime.json exists.
echo 4. Re-register both PIMETextService.dll files after copying.
echo 5. Ensure C:\Program Files (x86)\PIME\go-backend\input_methods\rime contains rime.dll.
echo 6. Start or restart PIMELauncher.exe after install.
echo.
exit /b 0

:prepare_rime_data
if exist "%PACKAGE_RIME_DATA_DIR%" (
    rmdir /s /q "%PACKAGE_RIME_DATA_DIR%"
)
mkdir "%PACKAGE_RIME_DATA_DIR%"
if errorlevel 1 (
    echo [ERROR] Failed to create packaged Rime data directory: "%PACKAGE_RIME_DATA_DIR%"
    exit /b 1
)

echo [INFO] Copying bundled rime-frost submodule data ...
xcopy "%RIME_DATA_DIR%" "%PACKAGE_RIME_DATA_DIR%\" /E /I /Y >nul
if errorlevel 1 (
    echo [ERROR] Failed to copy bundled Rime data from "%RIME_DATA_DIR%"
    exit /b 1
)

set "PLUM_DATA_PREPARED=0"

call :run_plum_install
if errorlevel 1 exit /b 1

if "%PLUM_DATA_PREPARED%"=="0" (
    echo [WARN] plum did not add preset shared data; falling back to Weasel shared data merge.
    call :merge_weasel_shared_data
    if errorlevel 1 (
        echo [ERROR] Failed to merge fallback Weasel shared data.
        exit /b 1
    )
)

call :copy_opencc_data
if errorlevel 1 exit /b 1

if exist "%RIME_DATA_DIR%\PIME.yaml" (
    copy /Y "%RIME_DATA_DIR%\PIME.yaml" "%PACKAGE_RIME_DATA_DIR%\PIME.yaml" >nul
)

echo [INFO] Packaged Rime shared data prepared at "%PACKAGE_RIME_DATA_DIR%"
exit /b 0

:merge_weasel_shared_data
call :find_weasel_data_dir
if not defined WEASEL_DATA_DIR (
    echo [WARN] Weasel shared data directory was not found; skip shared data merge.
    exit /b 0
)

echo [INFO] Merging Weasel shared data from "%WEASEL_DATA_DIR%"
xcopy "%WEASEL_DATA_DIR%\*.*" "%PACKAGE_RIME_DATA_DIR%\" /E /I /Y /D >nul
if errorlevel 1 (
    echo [ERROR] Failed to merge Weasel shared data from "%WEASEL_DATA_DIR%"
    exit /b 1
)
exit /b 0

:find_weasel_data_dir
if defined WEASEL_DATA_DIR (
    if exist "%WEASEL_DATA_DIR%\default.yaml" exit /b 0
    set "WEASEL_DATA_DIR="
)

if defined WEASEL_ROOT (
    if exist "%WEASEL_ROOT%\data\default.yaml" (
        set "WEASEL_DATA_DIR=%WEASEL_ROOT%\data"
        exit /b 0
    )
)

for %%K in ("HKLM\SOFTWARE\WOW6432Node\Rime\Weasel" "HKLM\SOFTWARE\Rime\Weasel" "HKCU\SOFTWARE\Rime\Weasel") do (
    for /f "tokens=2,*" %%A in ('reg query %%~K /v WeaselRoot 2^>nul ^| find "WeaselRoot"') do (
        set "WEASEL_ROOT=%%B"
        if exist "%%B\data\default.yaml" (
            set "WEASEL_DATA_DIR=%%B\data"
            exit /b 0
        )
    )
)

for %%D in ("%ProgramFiles%\Rime\weasel-*") do (
    if exist "%%~fD\data\default.yaml" set "WEASEL_DATA_DIR=%%~fD\data"
)
if defined WEASEL_DATA_DIR exit /b 0

if defined ProgramFiles(x86) (
    for %%D in ("%ProgramFiles(x86)%\Rime\weasel-*") do (
        if exist "%%~fD\data\default.yaml" set "WEASEL_DATA_DIR=%%~fD\data"
    )
)
exit /b 0

:run_plum_install
where bash >nul 2>nul
if errorlevel 1 (
    echo [WARN] bash was not found in PATH; skip plum/rime-install.
    exit /b 0
)

if exist "%PLUM_INSTALL%" (
    echo [INFO] Running plum/rime-install %PLUM_PRESET_TARGET% ...
    set "plum_dir=%PLUM_DIR%"
    set "rime_dir=%PACKAGE_RIME_DATA_DIR%"
    set "WSLENV=plum_dir:rime_dir"
    pushd "%PLUM_DIR%"
    bash rime-install %PLUM_PRESET_TARGET%
    set "PLUM_EXIT=%ERRORLEVEL%"
    popd
    if not "%PLUM_EXIT%"=="0" (
        echo [WARN] plum/rime-install failed; will fall back to Weasel shared data merge.
        exit /b 0
    )
    if exist "%PACKAGE_RIME_DATA_DIR%\essay.txt" (
        set "PLUM_DATA_PREPARED=1"
        exit /b 0
    )
    echo [WARN] plum/rime-install completed but did not install preset shared data into "%PACKAGE_RIME_DATA_DIR%"
)

if exist "%PLUM_INSTALL_BAT%" (
    echo [INFO] Running plum/rime-install.bat %PLUM_PRESET_TARGET% ...
    set "rime_dir=%PACKAGE_RIME_DATA_DIR%"
    pushd "%PLUM_DIR%"
    call "%PLUM_INSTALL_BAT%" %PLUM_PRESET_TARGET%
    set "PLUM_EXIT=%ERRORLEVEL%"
    popd
    if not "%PLUM_EXIT%"=="0" (
        echo [WARN] plum/rime-install.bat failed; will fall back to Weasel shared data merge.
        exit /b 0
    )
    if exist "%PACKAGE_RIME_DATA_DIR%\essay.txt" (
        set "PLUM_DATA_PREPARED=1"
    ) else (
        echo [WARN] plum/rime-install.bat completed but did not install preset shared data into "%PACKAGE_RIME_DATA_DIR%"
    )
)
exit /b 0

:copy_opencc_data
set "OPENCC_SOURCE="
call :find_weasel_data_dir
if defined WEASEL_DATA_DIR if exist "%WEASEL_DATA_DIR%\opencc\*.ocd*" set "OPENCC_SOURCE=%WEASEL_DATA_DIR%\opencc"
if not defined OPENCC_SOURCE if exist "%RIME_DATA_DIR%\opencc\*.ocd*" set "OPENCC_SOURCE=%RIME_DATA_DIR%\opencc"

if not defined OPENCC_SOURCE (
    echo [WARN] No OpenCC compiled data was found; packaged opencc directory remains unchanged.
    exit /b 0
)

if not exist "%PACKAGE_RIME_DATA_DIR%\opencc" mkdir "%PACKAGE_RIME_DATA_DIR%\opencc"
xcopy "%OPENCC_SOURCE%\*.*" "%PACKAGE_RIME_DATA_DIR%\opencc\" /E /I /Y >nul
if errorlevel 1 (
    echo [ERROR] Failed to copy OpenCC data from "%OPENCC_SOURCE%"
    exit /b 1
)
echo [INFO] Copied OpenCC data from "%OPENCC_SOURCE%"
exit /b 0
