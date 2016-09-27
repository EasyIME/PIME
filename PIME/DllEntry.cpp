#include "PIMEImeModule.h"
#include "resource.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <ShlObj.h>
#include <Shlwapi.h> // for PathIsRelative
#include <json/json.h>
#include "../libIME/Utils.h"


PIME::ImeModule* g_imeModule = NULL;

BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved) {
	switch (ul_reason_for_call) {
	case DLL_PROCESS_ATTACH:
		::DisableThreadLibraryCalls(hModule); // disable DllMain calls due to new thread creation
		//::MessageBox(0, L"X!", 0, 0);
		g_imeModule = new PIME::ImeModule(hModule);
		break;
	case DLL_PROCESS_DETACH:
		if(g_imeModule) {
			g_imeModule->Release();
			g_imeModule = NULL;
		}
		break;
	}
	return TRUE;
}

STDAPI DllCanUnloadNow(void) {
	return g_imeModule->canUnloadNow();
}

STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, void **ppvObj) {
	return g_imeModule->getClassObject(rclsid, riid, ppvObj);
}

STDAPI DllUnregisterServer(void) {
	return g_imeModule->unregisterServer();
}

static inline Ime::LangProfileInfo langProfileFromJson(std::wstring file, std::string& guid) {
	// load the json file to get the info of input method
	std::ifstream fp(file, std::ifstream::binary);
	if(fp) {
		Json::Value json;
		fp >> json;
		auto name = utf8ToUtf16(json["name"].asCString());
		guid = json["guid"].asCString();
		auto guidStr = utf8ToUtf16(guid.c_str());
		CLSID guid = {0};
		CLSIDFromString (guidStr.c_str(), &guid);
		// convert locale name to lanid
		auto locale = utf8ToUtf16(json["locale"].asCString());
		auto fallbackLocale = utf8ToUtf16(json["fallbackLocale"].asCString());
		// ::MessageBox(0, name.c_str(), 0, 0);
		auto iconFile = utf8ToUtf16(json["icon"].asCString());
		if (!iconFile.empty() && PathIsRelative(iconFile.c_str())) {
			int p = file.rfind('\\');
			if (p != file.npos) {
				iconFile = file.substr(0, p + 1) + iconFile;
			}
		}
		// ::MessageBox(0, iconFile.c_str(), 0, 0);
		Ime::LangProfileInfo langProfile = {
			name,
			guid,
			locale,
			fallbackLocale,
			iconFile
		};
		return langProfile;
	}
	return Ime::LangProfileInfo();
}

STDAPI DllRegisterServer(void) {
	int iconIndex = 0; // use classic icon
	if(g_imeModule->isWindows8Above())
		iconIndex = 1; // use Windows 8 style IME icon

	wchar_t modulePath[MAX_PATH];
	int len = ::GetModuleFileName(g_imeModule->hInstance(), modulePath, MAX_PATH);
	while(modulePath[len] != '\\')
		--len;
	modulePath[len] = '\0';
	// std::wstring dirPath = modulePath;
	std::vector<Ime::LangProfileInfo> langProfiles;
	std::wstring dirPath;
	// get the program data directory
	// try C:\program files (x86) first
	wchar_t path[MAX_PATH];
	HRESULT result = ::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILESX86, NULL, 0, path);
	if (result != S_OK) // failed, fall back to C:\program files
		result = ::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILES, NULL, 0, path);
	if (result == S_OK) { // program files folder is found
#ifndef _WIN64  // only for the 32-bit version
		// also update the profile_backends.cache file.
		std::wstring profile_backends = path;
		profile_backends += L"\\PIME\\profile_backends.cache";
		std::ofstream ofile(profile_backends);
#endif
		for (const auto backendDir : PIME::ImeModule::backendDirs_) {
			std::string backendName = utf16ToUtf8(backendDir);
			dirPath = path;
			dirPath += L"\\PIME\\";
			dirPath += backendDir;
			dirPath += L"\\input_methods";
			// scan the dir for lang profile definition files
			WIN32_FIND_DATA findData = { 0 };
			HANDLE hFind = ::FindFirstFile((dirPath + L"\\*").c_str(), &findData);
			if (hFind != INVALID_HANDLE_VALUE) {
				do {
					if (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) { // this is a subdir
						if (findData.cFileName[0] != '.') {
							std::wstring imejson = dirPath;
							imejson += '\\';
							imejson += findData.cFileName;
							imejson += L"\\ime.json";
							// Make sure the file exists
							DWORD fileAttrib = GetFileAttributesW(imejson.c_str());
							if (fileAttrib != INVALID_FILE_ATTRIBUTES) {
								// load the json file to get the info of input method
								std::string guid;
								langProfiles.push_back(std::move(langProfileFromJson(imejson, guid)));

#ifndef _WIN64  // only for the 32-bit version
								ofile << guid << "\t" << backendName << std::endl;
#endif
							}
						}
					}
				} while (::FindNextFile(hFind, &findData));
				CloseHandle(hFind);
			}
		}
	}
	return g_imeModule->registerServer(L"PIMETextService", langProfiles.data(), langProfiles.size());
}
