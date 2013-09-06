#ifndef DISPLAY_ATTRIBUTE_H
#define DISPLAY_ATTRIBUTE_H

#include <msctf.h>

namespace Ime {

class DisplayAttributeInfo : public ITfDisplayAttributeInfo {
public:
	DisplayAttributeInfo(void);
	virtual ~DisplayAttributeInfo(void);

    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
    STDMETHODIMP_(ULONG) AddRef(void);
    STDMETHODIMP_(ULONG) Release(void);

    // ITfDisplayAttributeInfo
    STDMETHODIMP GetGUID(GUID *pguid);
    STDMETHODIMP GetDescription(BSTR *pbstrDesc);
    STDMETHODIMP GetAttributeInfo(TF_DISPLAYATTRIBUTE *ptfDisplayAttr);
    STDMETHODIMP SetAttributeInfo(const TF_DISPLAYATTRIBUTE *ptfDisplayAttr);
    STDMETHODIMP Reset();

private:
	int refCount_;
	GUID guid_;
	wchar_t* desc_;
	TF_DISPLAYATTRIBUTE attrib_;
};

}

#endif
