#include "Utils.h"

#include <fstream>
#include <Windows.h>
#include <ShlObj.h>

namespace PIME {

bool loadJsonFile(const std::wstring filename, Json::Value& result) {
	std::ifstream fp(filename, std::ifstream::binary);
	if (fp) {
		fp >> result;
		return true;
	}
	return false;
}

bool saveJsonFile(const std::wstring filename, Json::Value& data) {
	std::ofstream fp(filename, std::ifstream::binary);
	if (fp) {
		fp << data;
		return true;
	}
	return false;
}

std::wstring getCurrentExecutableDir() {
    wchar_t exeFilePathBuf[MAX_PATH];
    DWORD len = GetModuleFileNameW(NULL, exeFilePathBuf, MAX_PATH);
    exeFilePathBuf[len] = '\0';

    // strip the filename part to get dir path
    wchar_t* p = wcsrchr(exeFilePathBuf, '\\');
    if (p) {
        *p = '\0';
    }
    return exeFilePathBuf;
}

std::wstring getAppLocalDir() {
    wchar_t* appLocalDataDirPath = nullptr;
    ::SHGetKnownFolderPath(FOLDERID_LocalAppData, 0, nullptr, &appLocalDataDirPath);
    std::wstring result{appLocalDataDirPath};
    ::CoTaskMemFree(appLocalDataDirPath);
    return result;
}

bool makeDirs(const std::wstring& path) {
    return ::SHCreateDirectoryEx(nullptr, path.c_str(), nullptr) == ERROR_SUCCESS;
}

std::string generateUuidStr() {
    UUID uuid;
    UuidCreate(&uuid);

    RPC_CSTR uuid_str = nullptr;
    UuidToStringA(&uuid, &uuid_str);
    std::string result = (char*)uuid_str;
    RpcStringFreeA(&uuid_str);
    return result;
}

} // namespace PIME
