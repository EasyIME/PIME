cmake . -Bbuild -G "Visual Studio 18 2026" -A Win32 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build --config Release

cmake . -Bbuild64 -G "Visual Studio 18 2026"  -A x64 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build64 --config Release --target PIMETextService

cmake . -Bbuild_arm64 -G "Visual Studio 18 2026"  -A ARM64 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build_arm64 --config Release --target PIMETextService

echo "Generating ARM64X forwarder..."
echo EXPORTS > build_arm64\arm64.def
echo DllCanUnloadNow=PIMETextService_arm64.DllCanUnloadNow >> build_arm64\arm64.def
echo DllGetClassObject=PIMETextService_arm64.DllGetClassObject >> build_arm64\arm64.def
echo DllRegisterServer=PIMETextService_arm64.DllRegisterServer >> build_arm64\arm64.def
echo DllUnregisterServer=PIMETextService_arm64.DllUnregisterServer >> build_arm64\arm64.def

echo EXPORTS > build_arm64\x64.def
echo DllCanUnloadNow=PIMETextService_x64.DllCanUnloadNow >> build_arm64\x64.def
echo DllGetClassObject=PIMETextService_x64.DllGetClassObject >> build_arm64\x64.def
echo DllRegisterServer=PIMETextService_x64.DllRegisterServer >> build_arm64\x64.def
echo DllUnregisterServer=PIMETextService_x64.DllUnregisterServer >> build_arm64\x64.def

cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"" x64_arm64 && link /dll /noentry /machine:arm64x /defArm64Native:build_arm64\arm64.def /def:build_arm64\x64.def /out:build_arm64\PIMETextService_forwarder.dll"

copy /y build_arm64\PIMETextService\Release\PIMETextService.dll build_arm64\PIMETextService\Release\PIMETextService_arm64.dll
copy /y build\PIMETextService\Release\PIMETextService.dll build_arm64\PIMETextService\Release\PIMETextService_x64.dll
copy /y build_arm64\PIMETextService_forwarder.dll build_arm64\PIMETextService\Release\PIMETextService.dll

echo "Start building McBopomofo"
cd McBopomofoWeb
cmd /C npm install
cmd /C npm run build:pime
cd ..

echo "Copy McBopomofo to node\input_methods\McBopomofo"
cmd /C rd /s /q node\input_methods\McBopomofo
cmd /C mkdir node\input_methods\McBopomofo
cmd /C xcopy /s /q /y /f McBopomofoWeb\output\pime node\input_methods\McBopomofo\.


echo "Start building McFoximWeb"
cd McFoximWeb
cmd /C npm install
cmd /C npm run build:pime
cd ..

echo "Copy McFoximWeb to node\input_methods\McFoxim"
cmd /C rd /s /q node\input_methods\McFoxim
cmd /C mkdir node\input_methods\McFoxim
cmd /C xcopy /s /q /y /f McFoximWeb\output\pime node\input_methods\McFoxim\.

echo "Start building McTabimWeb"
cd McTabimWeb
cmd /C npm install
cmd /C npm run build:pime
cd ..

echo "Copy McTabimWeb to node\input_methods\McTabim"
cmd /C rd /s /q node\input_methods\McTabim
cmd /C mkdir node\input_methods\McTabim
cmd /C xcopy /s /q /y /f McTabimWeb\output\pime node\input_methods\McTabim\.

echo "Start building PIME Installer"
cd installer
..\python\python3\python.exe stage_payload.py
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
..\python\python3\python.exe generate_harvest_wxs.py
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
    dotnet build PIME_WiX.sln -c Release
    if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
    
    echo "Creating single multilingual MSI..."
    cmd /C build_multilingual.bat
    if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
    cd ..

