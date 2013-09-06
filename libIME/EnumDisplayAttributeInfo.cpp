#include "EnumDisplayAttributeInfo.h"
#include <assert.h>

using namespace Ime;

EnumDisplayAttributeInfo::EnumDisplayAttributeInfo(TextService* service) {
}

EnumDisplayAttributeInfo::~EnumDisplayAttributeInfo(void) {
}

// IUnknown
STDMETHODIMP EnumDisplayAttributeInfo::QueryInterface(REFIID riid, void **ppvObj) {
    if (ppvObj == NULL)
        return E_INVALIDARG;

	if(IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_IEnumTfDisplayAttributeInfo))
		*ppvObj = (IEnumTfDisplayAttributeInfo*)this;
	else
		*ppvObj = NULL;

	if(*ppvObj) {
		AddRef();
		return S_OK;
	}
	return E_NOINTERFACE;
}

STDMETHODIMP_(ULONG) EnumDisplayAttributeInfo::AddRef(void) {
	return ++refCount_;
}

STDMETHODIMP_(ULONG) EnumDisplayAttributeInfo::Release(void) {
	assert(refCount_ > 0);
	--refCount_;
	if(0 == refCount_)
		delete this;
	return refCount_;
}


// IEnumTfDisplayAttributeInfo
STDMETHODIMP Clone(IEnumTfDisplayAttributeInfo **ppEnum) {
	return S_OK;
}

STDMETHODIMP Next(ULONG ulCount, ITfDisplayAttributeInfo **rgInfo, ULONG *pcFetched) {
	return S_OK;
}

STDMETHODIMP Reset() {
	return S_OK;
}

STDMETHODIMP Skip(ULONG ulCount) {
	return S_OK;
}
