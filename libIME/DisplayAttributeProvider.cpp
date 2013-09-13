#include "DisplayAttributeProvider.h"
#include "DisplayAttributeInfo.h"
#include "DisplayAttributeInfoEnum.h"
#include "ImeModule.h"
#include <assert.h>

using namespace Ime;
using namespace std;

DisplayAttributeProvider::DisplayAttributeProvider(ImeModule* module):
	imeModule_(module),
	refCount_(1) {
}

DisplayAttributeProvider::~DisplayAttributeProvider(void) {
}


// COM stuff

// IUnknown
STDMETHODIMP DisplayAttributeProvider::QueryInterface(REFIID riid, void **ppvObj) {
    if (ppvObj == NULL)
        return E_INVALIDARG;
	if(IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_ITfDisplayAttributeProvider))
		*ppvObj = (ITfDisplayAttributeProvider*)this;
	else
		*ppvObj = NULL;

	if(*ppvObj) {
		AddRef();
		return S_OK;
	}
	return E_NOINTERFACE;
}

// IUnknown implementation
STDMETHODIMP_(ULONG) DisplayAttributeProvider::AddRef(void) {
	return ++refCount_;
}

STDMETHODIMP_(ULONG) DisplayAttributeProvider::Release(void) {
	assert(refCount_ > 0);
	--refCount_;
	if(0 == refCount_)
		delete this;
	return refCount_;
}


// ITfDisplayAttributeProvider
STDMETHODIMP DisplayAttributeProvider::EnumDisplayAttributeInfo(IEnumTfDisplayAttributeInfo **ppEnum) {
	*ppEnum = (IEnumTfDisplayAttributeInfo*)new DisplayAttributeInfoEnum(this);
	return S_OK;
}

STDMETHODIMP DisplayAttributeProvider::GetDisplayAttributeInfo(REFGUID guidInfo, ITfDisplayAttributeInfo **ppInfo) {
	list<DisplayAttributeInfo*>& displayAttrInfos = imeModule_->displayAttrInfos();
	list<DisplayAttributeInfo*>::iterator it;
	for(it = displayAttrInfos.begin(); it != displayAttrInfos.end(); ++it) {
		DisplayAttributeInfo* info = *it;
		if(::IsEqualGUID(info->guid(), guidInfo)) {
			*ppInfo = info;
			info->AddRef();
			return S_OK;
		}
	}
	return E_INVALIDARG;
}
