cmake . -Bbuild -G "Visual Studio 17 2022" -A Win32 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build --config Release

cmake . -Bbuild64 -G "Visual Studio 17 2022"  -A x64 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build64 --config Release --target PIMETextService

cmake . -Bbuild_arm64 -G "Visual Studio 17 2022"  -A ARM64 -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build_arm64 --config Release --target PIMETextService


echo "Start building McBopomofo"
cd McBopomofoWeb
cmd /C npm install
cmd /C npm run build:pime
cd ..

echo "Copy McBopomofo to node\input_methods\McBopomofo"
cmd /C rd /s /q node\input_methods\McBopomofo
cmd /C mkdir node\input_methods\McBopomofo
cmd /C xcopy /s /q /y /f McBopomofoWeb\output\pime node\input_methods\McBopomofo\.
