cmake . -Bbuild -G "Visual Studio 17 2022" -A Win32
cmake --build build --config Release

cmake . -Bbuild64 -G "Visual Studio 17 2022"  -A x64
cmake --build build64 --config Release --target PIMETextService

echo "Start building McBopomofo"
cd McBopomofoWeb
cmd /C npm install
cmd /C npm run build:pime
cd ..

echo "Copy McBopomofo to node\input_methods\McBopomofo"
cmd /C rd /s /q node\input_methods\McBopomofo
cmd /C mkdir node\input_methods\McBopomofo
cmd /C xcopy /s /q /y /f McBopomofoWeb\output\pime node\input_methods\McBopomofo\.
