#include "DisplayAttributeInfo.h"
#include <assert.h>

using namespace Ime;

DisplayAttributeInfo::DisplayAttributeInfo(void):
	refCount_(1) {
}

DisplayAttributeInfo::~DisplayAttributeInfo(void) {
}

// COM stuff

// IUnknown
STDMETHODIMP DisplayAttributeInfo::QueryInterface(REFIID riid, void **ppvObj) {
    if (ppvObj == NULL)
        return E_INVALIDARG;

	if(IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_ITfDisplayAttributeInfo))
		*ppvObj = (ITfDisplayAttributeInfo*)this;
	else
		*ppvObj = NULL;

	if(*ppvObj) {
		AddRef();
		return S_OK;
	}
	return E_NOINTERFACE;
}

STDMETHODIMP_(ULONG) DisplayAttributeInfo::AddRef(void) {
	return ++refCount_;
}

STDMETHODIMP_(ULONG) DisplayAttributeInfo::Release(void) {
	assert(refCount_ > 0);
	--refCount_;
	if(0 == refCount_)
		delete this;
	return refCount_;
}

// ITfDisplayAttributeInfo
STDMETHODIMP DisplayAttributeInfo::GetGUID(GUID *pguid) {
	return S_OK;
}

STDMETHODIMP DisplayAttributeInfo::GetDescription(BSTR *pbstrDesc) {
	return S_OK;
}

STDMETHODIMP DisplayAttributeInfo::GetAttributeInfo(TF_DISPLAYATTRIBUTE *ptfDisplayAttr) {
	return S_OK;
}

STDMETHODIMP DisplayAttributeInfo::SetAttributeInfo(const TF_DISPLAYATTRIBUTE *ptfDisplayAttr) {
	return S_OK;
}

STDMETHODIMP DisplayAttributeInfo::Reset() {
	return S_OK;
}
