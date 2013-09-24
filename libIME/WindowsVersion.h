#ifndef IME_WINDOWS_VERSION_H
#define IME_WINDOWS_VERSION_H
#pragma once

#include <Windows.h>

namespace Ime {

// Reference: http://msdn.microsoft.com/en-us/library/windows/desktop/ms724832(v=vs.85).aspx

class WindowsVersion {
public:
	WindowsVersion(void) {
		// check Windows version (windows 8 is 6.2, and 7 is 6.1)
		DWORD winVer = ::GetVersion();
		major_ = (DWORD)(LOBYTE(LOWORD(winVer)));
		minor_ = (DWORD)(HIBYTE(LOWORD(winVer)));
	}

	~WindowsVersion(void) {
	}

	bool isWindows8Above() const {
		// Windows 8: 6.2
		return (major_ > 6 || (major_ == 6 && minor_ >= 2));
	}

	bool isWindows7() const {
		// Windows 7: 6.1
		// Windows server 2008 R2: 6.1
		return (major_ == 6 && minor_ == 1);
	}

	bool isWindowsVista() const {
		// Windows Vista: 6.0
		// Windows server 2008: 6.0
		return (major_ == 6 && minor_ == 0);
	}

	bool isWindowsXp() const {
		// Windows xp: 5.1
		// Windows xp 64 bit, server 2003: 5.2
		return (major_ == 5 && (minor_ == 1 || minor_ == 2));
	}

	DWORD major()  const {
		return major_;
	}

	DWORD minor() const {
		return minor_;
	}

private:
	DWORD major_;
	DWORD minor_;
};

}

#endif
