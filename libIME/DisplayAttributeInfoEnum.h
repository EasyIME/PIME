#ifndef ENUM_DISPLAY_ATTRIBUTE_INFO_H
#define ENUM_DISPLAY_ATTRIBUTE_INFO_H

#include <msctf.h>
#include <list>
#include "DisplayAttributeInfo.h"
#include "ComPtr.h"

namespace Ime {

class TextService;

class DisplayAttributeInfoEnum : public IEnumTfDisplayAttributeInfo {
public:
	DisplayAttributeInfoEnum(TextService* service);
	DisplayAttributeInfoEnum(const DisplayAttributeInfoEnum& other);
	virtual ~DisplayAttributeInfoEnum(void);

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
	std::list<DisplayAttributeInfo*>::iterator iterator_;
	ComPtr<TextService> textService_;
};

}

#endif
