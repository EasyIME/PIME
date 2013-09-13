#include "DisplayAttributeInfoEnum.h"
#include "TextService.h"
#include <assert.h>

using namespace Ime;

DisplayAttributeInfoEnum::DisplayAttributeInfoEnum(TextService* service):
	textService_(service),
	refCount_(1) {
	iterator_ = service->displayAttrInfos_.begin();
}

DisplayAttributeInfoEnum::DisplayAttributeInfoEnum(const DisplayAttributeInfoEnum& other):
	textService_(other.textService_),
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
	for(; i < ulCount; ++i) {
		if(iterator_ != textService_->displayAttrInfos_.end()) {
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
	iterator_ = textService_->displayAttrInfos_.begin();
	return S_OK;
}

STDMETHODIMP DisplayAttributeInfoEnum::Skip(ULONG ulCount) {
	if(iterator_ != textService_->displayAttrInfos_.end())
		++iterator_;
	return S_OK;
}
