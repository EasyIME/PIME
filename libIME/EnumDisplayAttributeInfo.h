#ifndef ENUM_DISPLAY_ATTRIBUTE_INFO_H
#define ENUM_DISPLAY_ATTRIBUTE_INFO_H

#include "msctf.h"

namespace Ime {

class TextService;

class EnumDisplayAttributeInfo : public IEnumTfDisplayAttributeInfo {
public:
	EnumDisplayAttributeInfo(TextService* service);
	virtual ~EnumDisplayAttributeInfo(void);

    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
    STDMETHODIMP_(ULONG) AddRef(void);
    STDMETHODIMP_(ULONG) Release(void);

    // IEnumTfDisplayAttributeInfo
    STDMETHODIMP Clone(IEnumTfDisplayAttributeInfo **ppEnum);
    STDMETHODIMP Next(ULONG ulCount, ITfDisplayAttributeInfo **rgInfo, ULONG *pcFetched);
    STDMETHODIMP Reset();
    STDMETHODIMP Skip(ULONG ulCount);

private:
	int refCount_;
};

}

#endif
