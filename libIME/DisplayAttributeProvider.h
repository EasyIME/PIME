#ifndef IME_DISPLAY_ATTRIBUTE_PROVIDER_H
#define IME_DISPLAY_ATTRIBUTE_PROVIDER_H

#include <msctf.h>
#include <list>
#include "ComPtr.h"

namespace Ime {

class ImeModule;
class DisplayAttributeInfo;

class DisplayAttributeProvider : public ITfDisplayAttributeProvider {
public:

	friend class DisplayAttributeInfoEnum;

	DisplayAttributeProvider(ImeModule* module);
	virtual ~DisplayAttributeProvider(void);

	// COM stuff

    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
	STDMETHODIMP_(ULONG) AddRef(void);
	STDMETHODIMP_(ULONG) Release(void);

	// ITfDisplayAttributeProvider
    STDMETHODIMP EnumDisplayAttributeInfo(IEnumTfDisplayAttributeInfo **ppEnum);
    STDMETHODIMP GetDisplayAttributeInfo(REFGUID guidInfo, ITfDisplayAttributeInfo **ppInfo);

private:
	int refCount_;
	ComPtr<ImeModule> imeModule_;
};

}

#endif


