#include "DisplayAttributeInfoEnum.h"
#include "DisplayAttributeProvider.h"
#include "ImeModule.h"
#include <assert.h>

using namespace Ime;

DisplayAttributeInfoEnum::DisplayAttributeInfoEnum(DisplayAttributeProvider* provider):
	provider_(provider),
	refCount_(1) {
	std::list<DisplayAttributeInfo*>& displayAttrInfos = provider_->imeModule_->displayAttrInfos();
	iterator_ = displayAttrInfos.begin();
}

DisplayAttributeInfoEnum::DisplayAttributeInfoEnum(const DisplayAttributeInfoEnum& other):
	provider_(other.provider_),
	iterator_(other.iterator_) {
}

DisplayAttributeInfoEnum::~DisplayAttributeInfoEnum(void) {
}

// IUnknown
STDMETHODIMP DisplayAttributeInfoEnum::QueryInterface(REFIID riid, void **ppvObj) {
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

STDMETHODIMP_(ULONG) DisplayAttributeInfoEnum::AddRef(void) {
	return ++refCount_;
}

STDMETHODIMP_(ULONG) DisplayAttributeInfoEnum::Release(void) {
	assert(refCount_ > 0);
	--refCount_;
	if(0 == refCount_)
		delete this;
	return refCount_;
}


// IEnumTfDisplayAttributeInfo
STDMETHODIMP DisplayAttributeInfoEnum::Clone(IEnumTfDisplayAttributeInfo **ppEnum) {
	*ppEnum = (IEnumTfDisplayAttributeInfo*)new DisplayAttributeInfoEnum(*this);
	return S_OK;
}

STDMETHODIMP DisplayAttributeInfoEnum::Next(ULONG ulCount, ITfDisplayAttributeInfo **rgInfo, ULONG *pcFetched) {
	ULONG i = 0;
	std::list<DisplayAttributeInfo*>& displayAttrInfos = provider_->imeModule_->displayAttrInfos();
	for(; i < ulCount; ++i) {
		if(iterator_ != displayAttrInfos.end()) {
			DisplayAttributeInfo* info = *iterator_;
			info->AddRef();
			rgInfo[i] = info;
			++iterator_;
		}
		else
			break;
	}
	if(pcFetched)
		*pcFetched = i;
	return S_OK;
}

STDMETHODIMP DisplayAttributeInfoEnum::Reset() {
	std::list<DisplayAttributeInfo*>& displayAttrInfos = provider_->imeModule_->displayAttrInfos();
	iterator_ = displayAttrInfos.begin();
	return S_OK;
}

STDMETHODIMP DisplayAttributeInfoEnum::Skip(ULONG ulCount) {
	std::list<DisplayAttributeInfo*>& displayAttrInfos = provider_->imeModule_->displayAttrInfos();
	if(iterator_ != displayAttrInfos.end())
		++iterator_;
	return S_OK;
}
