#include "ChewingImeModule.h"

Chewing::ImeModule* g_imeModule = NULL;

// CLSID of our Text service
// {13F2EF08-575C-4D8C-88E0-F67BB8052B84}
static const CLSID g_textServiceClsid = {
	0x13f2ef08, 0x575c, 0x4d8c, { 0x88, 0xe0, 0xf6, 0x7b, 0xb8, 0x5, 0x2b, 0x84 }
};

// GUID of our language profile
// {CE45F71D-CE79-41D1-967D-640B65A380E3}
static const GUID g_profileGuid = {
	0xce45f71d, 0xce79, 0x41d1, { 0x96, 0x7d, 0x64, 0xb, 0x65, 0xa3, 0x80, 0xe3 }
};

BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved) {
	switch (ul_reason_for_call) {
	case DLL_PROCESS_ATTACH:
		::DisableThreadLibraryCalls(hModule); // disable DllMain calls due to new thread creation
		g_imeModule = new Chewing::ImeModule(hModule);
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
	return g_imeModule->unregisterServer(g_textServiceClsid, g_profileGuid);
}

STDAPI DllRegisterServer(void) {
	return g_imeModule->registerServer(
		L"新酷音輸入法",
		g_textServiceClsid,
		g_profileGuid,
		MAKELANGID(LANG_CHINESE, SUBLANG_CHINESE_TRADITIONAL));
}
