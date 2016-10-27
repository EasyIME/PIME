cmake . -Bbuild -G"Visual Studio 14 2015"
cmake --build build --config Release

cmake . -Bbuild64 -G"Visual Studio 14 2015 Win64"
cmake --build build64 --config Release --target PIMETextService
