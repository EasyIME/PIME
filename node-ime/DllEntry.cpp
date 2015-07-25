#include "NodeImeModule.h"
#include "resource.h"
#include <iostream>
#include <vector>
#include "rapidjson/document.h"

Node::ImeModule* g_imeModule = NULL;

// GUID of our language profile
// {CE45F71D-CE79-41D1-967D-640B65A380E3}
static const GUID g_profileGuid = {
	0xce45f71d, 0xce79, 0x41d1, { 0x96, 0x7d, 0x64, 0xb, 0x65, 0xa3, 0x80, 0xe3 }
};

BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved) {
	switch (ul_reason_for_call) {
	case DLL_PROCESS_ATTACH:
		::DisableThreadLibraryCalls(hModule); // disable DllMain calls due to new thread creation
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
#if 0
	// load the json file to get the info of input method
	std::ifstream stream(file.c_str());
	if(stream.is_open()) {
		web::json::value json = web::json::value::parse(stream);
		stream.close();
		auto name = json[L"name"].as_string();
		auto guidStr = json[L"guid"].as_string();
		CLSID guid = {0};
		CLSIDFromString (guidStr.c_str(), &guid);
		// convert locale name to lanid
		LCID lcid = LocaleNameToLCID(json[L"locale"].as_string().c_str(), 0);
		LANGID langid = LANGIDFROMLCID(lcid);

		auto iconFile = json[L"icon"].as_string();
		Ime::LangProfileInfo langProfile = {
			name,
			guid,
			langid,
			iconFile
		};
		return std::move(langProfile);
	}
#endif
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
	std::wstring dirPath = L"D:\\node-ime\\server\\input-methods";

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
					imejson += '\\';
					imejson += L"ime.json";
					// load the json file to get the info of input method
					langProfiles.push_back(std::move(langProfileFromJson(imejson)));
				}
			}
		} while(::FindNextFile(hFind, &findData));
		CloseHandle(hFind);
	}
	return g_imeModule->registerServer(L"NodeTextService", langProfiles.data(), langProfiles.size());
}
