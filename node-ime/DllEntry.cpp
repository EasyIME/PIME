#include "NodeImeModule.h"
#include "resource.h"
#include <iostream>
#include <cstdio>
#include <vector>
#include <ShlObj.h>
#include <Shlwapi.h> // for PathIsRelative
#include "rapidjson/document.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/filereadstream.h"
#include "../libIME/Utils.h"

using namespace rapidjson;

Node::ImeModule* g_imeModule = NULL;

BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved) {
	switch (ul_reason_for_call) {
	case DLL_PROCESS_ATTACH:
		::DisableThreadLibraryCalls(hModule); // disable DllMain calls due to new thread creation
		//::MessageBox(0, L"X!", 0, 0);
		g_imeModule = new Node::ImeModule(hModule);
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

static Ime::LangProfileInfo langProfileFromJson(std::wstring file) {
	// load the json file to get the info of input method
	std::FILE* fp = _wfopen(file.c_str(), L"r");
	if(fp) {
		Document json;
		char buf[4096];
		FileReadStream stream(fp, buf, sizeof(buf));
		json.ParseStream(stream);
		fclose(fp);
		auto name = utf8ToUtf16(json["name"].GetString());
		auto guidStr = utf8ToUtf16(json["guid"].GetString());
		CLSID guid = {0};
		CLSIDFromString (guidStr.c_str(), &guid);
		// convert locale name to lanid
		auto locale = utf8ToUtf16(json["locale"].GetString());
		LCID lcid = LocaleNameToLCID(locale.c_str(), 0);
		LANGID langid = LANGIDFROMLCID(lcid);
		// ::MessageBox(0, name.c_str(), 0, 0);
		auto iconFile = utf8ToUtf16(json["icon"].GetString());
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
			langid,
			iconFile
		};
		return std::move(langProfile);
	}
	return std::move(Ime::LangProfileInfo());
}

STDAPI DllRegisterServer(void) {
	// ::LoadStringW(g_imeModule->hInstance(), IDS_CHEWING, name, 32);
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
		dirPath = path;
		dirPath += L"\\PIme\\server\\input_methods";
		// scan the dir for lang profile definition files
		WIN32_FIND_DATA findData = {0};
		HANDLE hFind = ::FindFirstFile((dirPath + L"\\*").c_str(), &findData);
		if(hFind != INVALID_HANDLE_VALUE) {
			do {
				if(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) { // this is a subdir
					if(findData.cFileName[0] != '.') {
						std::wstring imejson = dirPath;
						imejson += '\\';
						imejson += findData.cFileName;
						imejson += L"\\ime.json";
						// load the json file to get the info of input method
						langProfiles.push_back(std::move(langProfileFromJson(imejson)));
					}
				}
			} while(::FindNextFile(hFind, &findData));
			CloseHandle(hFind);
		}
	}
	return g_imeModule->registerServer(L"NodeTextService", langProfiles.data(), langProfiles.size());
}
