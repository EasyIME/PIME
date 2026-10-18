cmake . -Bbuild -G "Visual Studio 18 2026" -A Win32 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmake --build build --config Release
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

cmake . -Bbuild64 -G "Visual Studio 18 2026"  -A x64 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmake --build build64 --config Release --target PIMETextService
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

cmake . -Bbuild_arm64 -G "Visual Studio 18 2026"  -A ARM64 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmake --build build_arm64 --config Release --target PIMETextService
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%


echo "Start building McBopomofo"
cd McBopomofoWeb
cmd /C npm install
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmd /C npm run build:pime
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cd ..

echo "Copy McBopomofo to node\input_methods\McBopomofo"
cmd /C rd /s /q node\input_methods\McBopomofo
cmd /C mkdir node\input_methods\McBopomofo
cmd /C xcopy /s /q /y /f McBopomofoWeb\output\pime node\input_methods\McBopomofo\.
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmd /C del /q node\input_methods\McBopomofo\server.js node\input_methods\McBopomofo\webpack_check.js node\input_methods\McBopomofo\run_*.bat node\input_methods\McBopomofo\README.md node\input_methods\McBopomofo\*.txt

echo "Start building McFoximWeb"
cd McFoximWeb
cmd /C npm install
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmd /C npm run build:pime
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cd ..

echo "Copy McFoximWeb to node\input_methods\McFoxim"
cmd /C rd /s /q node\input_methods\McFoxim
cmd /C mkdir node\input_methods\McFoxim
cmd /C xcopy /s /q /y /f McFoximWeb\output\pime node\input_methods\McFoxim\.
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmd /C del /q node\input_methods\McFoxim\server.js node\input_methods\McFoxim\webpack_check.js node\input_methods\McFoxim\run_*.bat node\input_methods\McFoxim\README.md node\input_methods\McFoxim\*.txt

echo "Start building McTabimWeb"
cd McTabimWeb
cmd /C npm install
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmd /C npm run build:pime
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cd ..

echo "Copy McTabimWeb to node\input_methods\McTabim"
cmd /C rd /s /q node\input_methods\McTabim
cmd /C mkdir node\input_methods\McTabim
cmd /C xcopy /s /q /y /f McTabimWeb\output\pime node\input_methods\McTabim\.
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmd /C del /q node\input_methods\McTabim\server.js node\input_methods\McTabim\webpack_check.js node\input_methods\McTabim\run_*.bat node\input_methods\McTabim\README.md node\input_methods\McTabim\*.txt

echo "Start building emojime"
cd node\input_methods\emojime
cmd /C npm install
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmd /C npm run build
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cd ..\..\..


