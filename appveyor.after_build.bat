setlocal

cd installer
..\python\python3\python.exe generate_harvest_wxs.py
if %ERRORLEVEL% NEQ 0 goto ERROR
dotnet build PIME_WiX.sln -c Release
if %ERRORLEVEL% NEQ 0 goto ERROR
cd ..

:ERROR
set EXITCODE=%ERRORLEVEL%

:EXIT
exit /b %EXITCODE%
