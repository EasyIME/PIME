#include "EditSession.h"
#include "TextService.h"
#include <assert.h>

using namespace Ime;

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
