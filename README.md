# windows-TSF-chewing

Implement chewing in Windows via Text Services Framework.

# Development

## Tool Requirements
*   [CMake](http://www.cmake.org/) >= 2.8.8
*   [Visual Studio Express 2012](http://www.microsoft.com/visualstudio/eng/products/visual-studio-express-products)
*   [git](http://windows.github.com/)
*   Editor with [EditorConfig](http://editorconfig.org/) supported

## How to Build
*   Get source from github

        git clone https://github.com/chewing/windows-TSF-chewing.git
        cd windows-TSF-chewing
        git submodule init
        git submodule update

*   Use CMake to generate Visual Studio project

        cmake -G "Visual Studio 11" <path to windows-TSF-chewing>
        cmake -G "Visual Studio 11 Win64" <path to windows-TSF-chewing>

*   Open generated project with Visual Studio and build it

## References
*   [Text Services Framework](http://msdn.microsoft.com/en-us/library/windows/desktop/ms629032%28v=vs.85%29.aspx)
*   [Guidelines and checklist for IME development (Windows Store apps)](http://msdn.microsoft.com/en-us/library/windows/apps/hh967425.aspx)
*   [Strategies for App Communication between Windows 8 UI and Windows 8 Desktop](http://software.intel.com/en-us/articles/strategies-for-app-communication-between-windows-8-ui-and-windows-8-desktop)

# Install
*   Copy `external/libchewing/data/*.dat` to `%WINDIR%/chewing`
*   Use `regsvr32` to register `ChewingService.dll`. 64-bit system need to register both 32-bit and 64-bit `ChewingService.dll`

        regsvr32 ChewingService.dll (run as administrator)

# Bug Report
Please report any issue to [here](https://github.com/chewing/windows-TSF-chewing/issues).
