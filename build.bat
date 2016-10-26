mkdir build
cd build
cmake -G "Visual Studio 14 2015" ..
cmake --build . --config Release
cd ..

mkdir build64
cd build64
cmake -G "Visual Studio 14 2015 Win64" ..
cmake --build . --config Release --target PIMETextService
cd ..

cd installer
makensis installer.nsi
pause