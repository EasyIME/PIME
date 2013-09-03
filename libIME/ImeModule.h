#ifndef IME_MODULE_H
#define IME_MODULE_H

#include <Unknwn.h>

namespace Ime {

class TextService;

class ImeModule: public IClassFactory {
public:
	ImeModule(HMODULE module);
	virtual ~ImeModule(void);

	// public methods
	HINSTANCE hInstance() const {
		return hInstance_;
	}

	// Dll entry points implementations
	HRESULT canUnloadNow();
	HRESULT getClassObject(REFCLSID rclsid, REFIID riid, void **ppvObj);
	HRESULT registerServer(wchar_t* name, const CLSID& textServiceClsid, const GUID& profileGuid, LANGID languageId);
	HRESULT unregisterServer(const CLSID& textServiceClsid, const GUID& profileGuid);

	virtual TextService* createTextService() = 0;

	// COM-related stuff

	// IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
    STDMETHODIMP_(ULONG) AddRef(void);
    STDMETHODIMP_(ULONG) Release(void);

protected:
    // IClassFactory
    STDMETHODIMP CreateInstance(IUnknown *pUnkOuter, REFIID riid, void **ppvObj);
    STDMETHODIMP LockServer(BOOL fLock);

private:
	int refCount_;
	HINSTANCE hInstance_;
};

}

#endif
