#include "PIMEImeModule.h"
#include "JsonUtils.h"
#include "resource.h"

#include <fstream>
#include <mutex>
#include <optional>
#include <vector>

#include <ShlObj.h>
#include <Shlwapi.h> // for PathIsRelative
#include <VersionHelpers.h>  // Provided by Windows SDK >= 8.1

#include <nlohmann/json.hpp>
#include "../libIME2/src/Utils.h"

using json = nlohmann::json;
using PIME::jsonValueOr;
using PIME::parseJsonNoThrow;

static HMODULE g_hModule = NULL;
static PIME::ImeModule* g_imeModule = NULL;
static std::mutex g_imeModuleMutex;

static PIME::ImeModule* getImeModule() {
	std::lock_guard<std::mutex> lock(g_imeModuleMutex);
	if (!g_imeModule && g_hModule) {
		g_imeModule = new PIME::ImeModule(g_hModule);
	}
	return g_imeModule;
}

static void releaseImeModule() {
	std::lock_guard<std::mutex> lock(g_imeModuleMutex);
	if (g_imeModule) {
		g_imeModule->Release();
		g_imeModule = NULL;
	}
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved) {
	switch (ul_reason_for_call) {
	case DLL_PROCESS_ATTACH:
		::DisableThreadLibraryCalls(hModule); // disable DllMain calls due to new thread creation
		g_hModule = hModule;
		break;
	case DLL_PROCESS_DETACH:
		// When lpReserved != NULL, the process is terminating (ExitProcess).
		// Per Microsoft DLL Best Practices, other threads and dependent DLLs (e.g. COM/CRT)
		// may already have been terminated or unloaded, and the OS will automatically reclaim
		// all process memory. Calling COM Release() or destructors during process exit risks
		// deadlocks or access violations. Therefore, we only perform cleanup on dynamic unload
		// (FreeLibrary, where lpReserved is NULL).
		// Reference: https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-best-practices
		if (lpReserved == NULL) {
			releaseImeModule();
		}
		g_hModule = NULL;
		break;
	}
	return TRUE;
}

STDAPI DllCanUnloadNow(void) {
	std::lock_guard<std::mutex> lock(g_imeModuleMutex);
	if (!g_imeModule) {
		return S_OK;
	}
	return g_imeModule->canUnloadNow();
}

STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, void **ppvObj) {
	auto module = getImeModule();
	return module ? module->getClassObject(rclsid, riid, ppvObj) : E_FAIL;
}

STDAPI DllUnregisterServer(void) {
	auto module = getImeModule();
	return module ? module->unregisterServer() : E_FAIL;
}

static inline std::optional<Ime::LangProfileInfo> langProfileFromJson(const std::wstring& file, int iconIndex) {
	// load the json file to get the info of input method
	std::ifstream fp(file, std::ifstream::binary);
	if (!fp) {
		return std::nullopt;
	}

	json j = parseJsonNoThrow(fp);
	if (!j.is_object() || j.is_discarded()) {
		return std::nullopt;
	}

	auto name = utf8ToUtf16(jsonValueOr<std::string>(j, "name", "").c_str());
	auto guid = jsonValueOr<std::string>(j, "guid", "");
	if (name.empty() || guid.empty()) {
		return std::nullopt;
	}

	CLSID clsidGuid = {0};
	if (FAILED(CLSIDFromString(utf8ToUtf16(guid.c_str()).c_str(), &clsidGuid))) {
		return std::nullopt;
	}

	// convert locale name to lanid
	auto locale = utf8ToUtf16(jsonValueOr<std::string>(j, "locale", "").c_str());
	auto fallbackLocale = utf8ToUtf16(jsonValueOr<std::string>(j, "fallbackLocale", "").c_str());
	auto iconFile = utf8ToUtf16(jsonValueOr<std::string>(j, "icon", "").c_str());
	if (!iconFile.empty() && PathIsRelative(iconFile.c_str())) {
		size_t p = file.rfind(L'\\');
		if (p != file.npos) {
			iconFile = file.substr(0, p + 1) + iconFile;
		}
	}
	return Ime::LangProfileInfo{
		std::move(name),
		clsidGuid,
		std::move(locale),
		std::move(fallbackLocale),
		std::move(iconFile),
		iconIndex
	};
}

STDAPI DllRegisterServer(void) {
	int iconIndex = 0; // use classic icon
	if(::IsWindows8OrGreater()) {
		iconIndex = 1; // use Windows 8 style IME icon
	}
	std::vector<Ime::LangProfileInfo> langProfiles;
	auto module = getImeModule();
	if (!module) {
		return E_FAIL;
	}
	const std::wstring programDir = module->programDir();
	for (const auto backendDir: module->backendDirs()) {
		std::string backendName = utf16ToUtf8(backendDir.c_str());
		std::wstring dirPath = programDir;
		dirPath += L'\\';
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
							if (auto profile = langProfileFromJson(imejson, iconIndex)) {
								langProfiles.push_back(std::move(*profile));
							}
						}
					}
				}
			} while (::FindNextFile(hFind, &findData));
			::FindClose(hFind);
		}
	}
	wchar_t modulePath[MAX_PATH];
	DWORD len = ::GetModuleFileNameW(g_hModule, modulePath, MAX_PATH);
	if (len == 0 || len >= MAX_PATH) {
		return E_FAIL;
	}
#if defined(_M_ARM64) || defined(__aarch64__)
	// On Windows 11 on ARM64, native ARM64 and emulated x64 (ARM64EC) host processes
	// share a single 64-bit COM registry space (InprocServer32). To support both
	// architectures under one CLSID, an ARM64X forwarder DLL is used:
	// https://learn.microsoft.com/en-us/windows/arm/arm64x-pe
	//
	// An ARM64X forwarder DLL contains no implementation code; the Windows PE loader
	// uses its dual export tables to automatically forward calls to either the native
	// ARM64 DLL or the x64 DLL depending on the host process architecture:
	// - <name>.dll: ARM64X forwarder DLL registered in InprocServer32
	// - <name>_arm64.dll: native ARM64 implementation
	// - <name>_x64.dll: x64 implementation for emulated processes
	//
	// When regsvr32 registers the server, execution enters the native ARM64 DLL.
	// Strip the "_arm64" suffix so InprocServer32 points to the forwarder DLL (<name>.dll),
	// allowing emulated x64 processes to also load the COM server.
	if (::PathMatchSpecW(modulePath, L"*_arm64.dll")) {
		constexpr size_t suffixLen = 10; // wcslen(L"_arm64.dll")
		wcscpy_s(modulePath + len - suffixLen, 5, L".dll");
	}
#endif
	return module->registerServer(L"PIMETextService", langProfiles.data(), static_cast<int>(langProfiles.size()), modulePath);
}
