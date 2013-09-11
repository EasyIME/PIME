#include "ImeModule.h"
#include <string>
#include <ObjBase.h>
#include <msctf.h>
#include <Shlwapi.h>
#include <assert.h>
#include "Window.h"

using namespace Ime;
using namespace std;

ImeModule::ImeModule(HMODULE module, const CLSID& textServiceClsid):
	hInstance_(HINSTANCE(module)),
	textServiceClsid_(textServiceClsid),
	refCount_(1) {

	Window::registerClass(hInstance_);
}

ImeModule::~ImeModule(void) {
}

// Dll entry points implementations
HRESULT ImeModule::canUnloadNow() {
	// we own the last reference
	return refCount_ <= 1 ? S_OK : S_FALSE;
}

HRESULT ImeModule::getClassObject(REFCLSID rclsid, REFIID riid, void **ppvObj) {
    if (IsEqualIID(riid, IID_IClassFactory) || IsEqualIID(riid, IID_IUnknown)) {
		// increase reference count
		AddRef();
		*ppvObj = (IClassFactory*)this; // our own object implements IClassFactory
		return NOERROR;
    }
	else
	    *ppvObj = NULL;
    return CLASS_E_CLASSNOTAVAILABLE;
}

HRESULT ImeModule::registerServer(wchar_t* name, const GUID& profileGuid, LANGID languageId) {
	// write info of our COM text service component to the registry
	// path: HKEY_CLASS_ROOT\\CLSID\\{xxxx-xxxx-xxxx-xx....}
	// This reguires Administrator permimssion to write to the registery
	// regsvr32 should be run with Administrator
	// For 64 bit dll, it seems that we need to write the key to
	// a different path to make it coexist with 32 bit version:
	// HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Classes\CLSID\{xxx-xxx-...}
	// Reference: http://stackoverflow.com/questions/1105031/can-my-32-bit-and-64-bit-com-components-co-reside-on-the-same-machine

	HRESULT result = S_OK;

	// get path of our module
	wchar_t modulePath[MAX_PATH];
	DWORD modulePathLen = GetModuleFileNameW(hInstance_, modulePath, MAX_PATH);

	wstring regPath = L"CLSID\\";
	LPOLESTR clsidStr = NULL;
	if(StringFromCLSID(textServiceClsid_, &clsidStr) != ERROR_SUCCESS)
		return E_FAIL;
	regPath += clsidStr;
	CoTaskMemFree(clsidStr);

	HKEY hkey = NULL;
	if(::RegCreateKeyExW(HKEY_CLASSES_ROOT, regPath.c_str(), 0, NULL, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &hkey, NULL) == ERROR_SUCCESS) {
		// write name of our IME
		::RegSetValueExW(hkey, NULL, 0, REG_SZ, (BYTE*)name, sizeof(wchar_t) * (wcslen(name) + 1));

		HKEY inProcServer32Key;
		if(::RegCreateKeyExW(hkey, L"InprocServer32", 0, NULL, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &inProcServer32Key, NULL) == ERROR_SUCCESS) {
			// store the path of our dll module in the registry
			::RegSetValueExW(inProcServer32Key, NULL, 0, REG_SZ, (BYTE*)modulePath, (modulePathLen + 1) * sizeof(wchar_t));
			// write threading model
			wchar_t apartmentStr[] = L"Apartment";
            ::RegSetValueExW(inProcServer32Key, L"ThreadingModel", 0, REG_SZ, (BYTE*)apartmentStr, 10 * sizeof(wchar_t));
			::RegCloseKey(inProcServer32Key);
		}
		else
			result = E_FAIL;
		::RegCloseKey(hkey);
    }
	else
		result = E_FAIL;

	// register the language profile
	if(result == S_OK) {
		result = E_FAIL;
		ITfInputProcessorProfiles *inputProcessProfiles = NULL;
		if(CoCreateInstance(CLSID_TF_InputProcessorProfiles, NULL, CLSCTX_INPROC_SERVER, IID_ITfInputProcessorProfiles, (void**)&inputProcessProfiles) == S_OK) {
			if(inputProcessProfiles->Register(textServiceClsid_) == S_OK) {
				if(inputProcessProfiles->AddLanguageProfile(textServiceClsid_, languageId, profileGuid,
											name, -1, modulePath, modulePathLen, 0) == S_OK) {
					result = S_OK;
				}
			}
			inputProcessProfiles->Release();
		}
	}

	// register category
	if(result == S_OK) {
		ITfCategoryMgr *categoryMgr = NULL;
		if(CoCreateInstance(CLSID_TF_CategoryMgr, NULL, CLSCTX_INPROC_SERVER, IID_ITfCategoryMgr, (void**)&categoryMgr) == S_OK) {
			if(categoryMgr->RegisterCategory(textServiceClsid_, GUID_TFCAT_TIP_KEYBOARD, textServiceClsid_) != S_OK) {
				result = E_FAIL;
			}

			// register ourself as a display attribute provider
			// so later we can set change the look and feels of composition string.
			//if(categoryMgr->RegisterCategory(textServiceClsid_, GUID_TFCAT_DISPLAYATTRIBUTEPROVIDER, textServiceClsid) != S_OK) {
			//	result = E_FAIL;
			//}

			// for Windows 8 store app support
			// TODO: according to a exhaustive Google search, I found that
			// TF_IPP_CAPS_IMMERSIVESUPPORT is required to make the IME work with Windows 8.
			// http://social.msdn.microsoft.com/Forums/windowsapps/en-US/4c422cf1-ceb4-413b-8a7c-6881946a4c63/how-to-set-a-flag-indicating-tsf-components-compatibility
			// Quote from the page: "To indicate that your IME is compatible with Windows Store apps, call RegisterCategory with GUID_TFCAT_TIPCAP_IMMERSIVESUPPORT."

			// declare supporting immersive mode
			if(categoryMgr->RegisterCategory(textServiceClsid_, GUID_TFCAT_TIPCAP_IMMERSIVESUPPORT, textServiceClsid_) != S_OK) {
				result = E_FAIL;
			}

			// declare compatibility with Windows 8 system tray
			if(categoryMgr->RegisterCategory(textServiceClsid_, GUID_TFCAT_TIPCAP_SYSTRAYSUPPORT, textServiceClsid_) != S_OK) {
				result = E_FAIL;
			}
			categoryMgr->Release();
		}
	}
	return result;
}

HRESULT ImeModule::unregisterServer(const GUID& profileGuid) {
	// unregister the language profile
	ITfInputProcessorProfiles *inputProcessProfiles = NULL;
	if(CoCreateInstance(CLSID_TF_InputProcessorProfiles, NULL, CLSCTX_INPROC_SERVER, IID_ITfInputProcessorProfiles, (void**)&inputProcessProfiles) == S_OK) {
		inputProcessProfiles->Unregister(textServiceClsid_);
		inputProcessProfiles->Release();
	}

	// unregister categories
	ITfCategoryMgr *categoryMgr = NULL;
	if(CoCreateInstance(CLSID_TF_CategoryMgr, NULL, CLSCTX_INPROC_SERVER, IID_ITfCategoryMgr, (void**)&categoryMgr) == S_OK) {
		categoryMgr->UnregisterCategory(textServiceClsid_, GUID_TFCAT_TIP_KEYBOARD, textServiceClsid_);
		categoryMgr->Release();
	}

	// delete the registry key
	wstring regPath = L"CLSID\\";
	LPOLESTR clsidStr = NULL;
	if(StringFromCLSID(textServiceClsid_, &clsidStr) == ERROR_SUCCESS) {
		regPath += clsidStr;
		CoTaskMemFree(clsidStr);
		::SHDeleteKey(HKEY_CLASSES_ROOT, regPath.c_str());
	}
	return S_OK;
}

// COM related stuff

// IUnknown
STDMETHODIMP ImeModule::QueryInterface(REFIID riid, void **ppvObj) {
    if (ppvObj == NULL)
        return E_INVALIDARG;

	if(IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_IClassFactory))
		*ppvObj = (IClassFactory*)this;
	else
		*ppvObj = NULL;

	if(*ppvObj) {
		AddRef();
		return S_OK;
	}
	return E_NOINTERFACE;
}

STDMETHODIMP_(ULONG) ImeModule::AddRef(void) {
	return ::InterlockedIncrement(&refCount_);
}

STDMETHODIMP_(ULONG) ImeModule::Release(void) {
	// NOTE: I think we do not need to use critical sections to
	// protect the operation as M$ did in their TSF samples.
	// Our ImeModule will be alive until dll unload so
	// it's not possible for an user application and TSF manager
	// to free our objecet since we always have refCount == 1.
	// The last reference is released in DllMain() when unloading.
	// Hence interlocked operations are enough here, I guess.
	assert(refCount_ > 0);
	if(::InterlockedExchangeSubtract(&refCount_, 1) == 1) {
		delete this;
	}
	return refCount_;
}

// IClassFactory
STDMETHODIMP ImeModule::CreateInstance(IUnknown *pUnkOuter, REFIID riid, void **ppvObj) {
	// FIXME: do we need to check riid here?
	TextService* service = createTextService();
	if(service) {
		*ppvObj = (void*)service;
		return S_OK;
	}
	return S_FALSE;
}

STDMETHODIMP ImeModule::LockServer(BOOL fLock) {
	if(fLock)
		AddRef();
	else
		Release();
	return S_OK;
}
