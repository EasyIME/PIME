//
//	Copyright (C) 2013 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
//
//	This library is free software; you can redistribute it and/or
//	modify it under the terms of the GNU Library General Public
//	License as published by the Free Software Foundation; either
//	version 2 of the License, or (at your option) any later version.
//
//	This library is distributed in the hope that it will be useful,
//	but WITHOUT ANY WARRANTY; without even the implied warranty of
//	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//	Library General Public License for more details.
//
//	You should have received a copy of the GNU Library General Public
//	License along with this library; if not, write to the
//	Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
//	Boston, MA  02110-1301, USA.
//

#include "DisplayAttributeInfoEnum.h"
#include "DisplayAttributeProvider.h"
#include "ImeModule.h"
#include <assert.h>

namespace Ime {

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

} // namespace Ime

