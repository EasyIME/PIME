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

#include "EditSession.h"
#include "TextService.h"
#include <assert.h>

namespace Ime {

EditSession::EditSession(TextService* service, ITfContext* context):
	textService_(service),
	context_(context),
	editCookie_(0),
	refCount_(1) {
	if(textService_)
		textService_->AddRef();
	if(context_)
		context_->AddRef();
}

EditSession::~EditSession(void) {
	if(textService_)
		textService_->Release();
	if(context_)
		context_->Release();
}

// COM stuff

// IUnknown
STDMETHODIMP EditSession::QueryInterface(REFIID riid, void **ppvObj) {
    if (ppvObj == NULL)
        return E_INVALIDARG;

	if(IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_ITfEditSession))
		*ppvObj = (ITfEditSession*)this;
	else
		*ppvObj = NULL;

	if(*ppvObj) {
		AddRef();
		return S_OK;
	}
	return E_NOINTERFACE;
}

// IUnknown implementation
STDMETHODIMP_(ULONG) EditSession::AddRef(void) {
	return ++refCount_;
}

STDMETHODIMP_(ULONG) EditSession::Release(void) {
	assert(refCount_ > 0);
	--refCount_;
	if(0 == refCount_)
		delete this;
	return refCount_;
}

STDMETHODIMP EditSession::DoEditSession(TfEditCookie ec) {
	editCookie_ = ec;
	return S_OK;
}

} // namespace Ime
