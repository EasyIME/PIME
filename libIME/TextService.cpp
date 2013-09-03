#include "TextService.h"
#include "EditSession.h"

#include <assert.h>

using namespace Ime;

TextService::TextService(void):
	threadMgr_(NULL),
	clientId_(TF_CLIENTID_NULL),
	threadMgrEventSinkCookie_(TF_INVALID_COOKIE),
	textEditSinkCookie_(TF_INVALID_COOKIE),
	compositionSinkCookie_(TF_INVALID_COOKIE),
	refCount_(1) {
}

TextService::~TextService(void) {
}

// public methods
void TextService::replaceSelectedText(wchar_t* str, int len) {
	// threadMgr_
}


// virtual
void TextService::onActivate() {
}

// virtual
void TextService::onDeactivate() {
}

// virtual
bool TextService::onKeyDown(long key) {
	return false;
}

// virtual
bool TextService::onKeyUp(long key) {
	return false;
}

// virtual
void TextService::onFocus() {

}


// COM stuff

// IUnknown
STDMETHODIMP TextService::QueryInterface(REFIID riid, void **ppvObj) {
    if (ppvObj == NULL)
        return E_INVALIDARG;

	if(IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_ITfTextInputProcessor))
		*ppvObj = (ITfTextInputProcessor*)this;
	else if(IsEqualIID(riid, IID_ITfDisplayAttributeProvider))
		*ppvObj = (ITfDisplayAttributeProvider*)this;
	else if(IsEqualIID(riid, IID_ITfThreadMgrEventSink))
		*ppvObj = (ITfThreadMgrEventSink*)this;
	else if(IsEqualIID(riid, IID_ITfTextEditSink))
		*ppvObj = (ITfTextEditSink*)this;
	else if(IsEqualIID(riid, IID_ITfKeyEventSink))
		*ppvObj = (ITfKeyEventSink*)this;
	else if(IsEqualIID(riid, IID_ITfCompositionSink))
		*ppvObj = (ITfCompositionSink*)this;
	else
		*ppvObj = NULL;

	if(*ppvObj) {
		AddRef();
		return S_OK;
	}
	return E_NOINTERFACE;
}

// IUnknown implementation
STDMETHODIMP_(ULONG) TextService::AddRef(void) {
	return ++refCount_;
}

STDMETHODIMP_(ULONG) TextService::Release(void) {
	assert(refCount_ > 0);
	--refCount_;
	if(0 == refCount_)
		delete this;
	return refCount_;
}

// ITfTextInputProcessor
STDMETHODIMP TextService::Activate(ITfThreadMgr *pThreadMgr, TfClientId tfClientId) {
	// store tsf manager & client id
	threadMgr_ = pThreadMgr;
	threadMgr_->AddRef();
	clientId_ = tfClientId;

	// advice event sinks (set up event listeners)
	
	// ITfThreadMgrEventSink
	ITfSource *source;
	if(threadMgr_->QueryInterface(IID_ITfSource, (void **)&source) != S_OK)
		goto OnError;
	source->AdviseSink(IID_ITfThreadMgrEventSink, (ITfThreadMgrEventSink *)this, &threadMgrEventSinkCookie_);
	source->Release();

	// ITfTextEditSink,

	// ITfKeyEventSink
	ITfKeystrokeMgr *keystrokeMgr;
	if (threadMgr_->QueryInterface(IID_ITfKeystrokeMgr, (void **)&keystrokeMgr) != S_OK)
		goto OnError;
	keystrokeMgr->AdviseKeyEventSink(clientId_, (ITfKeyEventSink*)this, TRUE);
	keystrokeMgr->Release();

	// ITfCompositionSink

	onActivate();

	return S_OK;

OnError:
	Deactivate();
	return E_FAIL;
}

STDMETHODIMP TextService::Deactivate() {

	onDeactivate();

	// unadvice event sinks

	// ITfThreadMgrEventSink
	ITfSource *source;
	if(threadMgr_->QueryInterface(IID_ITfSource, (void **)&source) == S_OK) {
		source->UnadviseSink(threadMgrEventSinkCookie_);
		source->Release();
		threadMgrEventSinkCookie_ = TF_INVALID_COOKIE;
	}

	// ITfTextEditSink,

	// ITfKeyEventSink
	ITfKeystrokeMgr *keystrokeMgr;
	if (threadMgr_->QueryInterface(IID_ITfKeystrokeMgr, (void **)&keystrokeMgr) == S_OK) {
		keystrokeMgr->UnadviseKeyEventSink(clientId_);
		keystrokeMgr->Release();
	}

	// ITfCompositionSink

	if(threadMgr_) {
		threadMgr_->Release();
		threadMgr_ = NULL;
	}
	clientId_ = TF_CLIENTID_NULL;
	return S_OK;
}


// ITfThreadMgrEventSink
STDMETHODIMP TextService::OnInitDocumentMgr(ITfDocumentMgr *pDocMgr) {
	::MessageBoxW(0, L"OnInitDocumentMgr", 0, 0);
	return S_OK;
}

STDMETHODIMP TextService::OnUninitDocumentMgr(ITfDocumentMgr *pDocMgr) {
	::MessageBoxW(0, L"OnUninitDocumentMgr", 0, 0);
	return S_OK;
}

STDMETHODIMP TextService::OnSetFocus(ITfDocumentMgr *pDocMgrFocus, ITfDocumentMgr *pDocMgrPrevFocus) {
	onFocus();
	return S_OK;
}

STDMETHODIMP TextService::OnPushContext(ITfContext *pContext) {
	::MessageBoxW(0, L"OnPushContext", 0, 0);
	return S_OK;
}

STDMETHODIMP TextService::OnPopContext(ITfContext *pContext) {
	::MessageBoxW(0, L"OnPopContext", 0, 0);
	return S_OK;
}


// ITfTextEditSink
STDMETHODIMP TextService::OnEndEdit(ITfContext *pContext, TfEditCookie ecReadOnly, ITfEditRecord *pEditRecord) {
	return S_OK;
}


// ITfKeyEventSink
STDMETHODIMP TextService::OnSetFocus(BOOL fForeground) {
	return S_OK;
}

STDMETHODIMP TextService::OnTestKeyDown(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pfEaten) {
	*pfEaten = TRUE;
	return S_OK;
}

STDMETHODIMP TextService::OnKeyDown(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pfEaten) {
	HRESULT sessionResult;
	KeyEditSession* session = new KeyEditSession(this, pContext, wParam, lParam);
	pContext->RequestEditSession(clientId_, session, TF_ES_SYNC|TF_ES_READWRITE, &sessionResult);
	session->Release();
	return S_OK;
}

STDMETHODIMP TextService::OnTestKeyUp(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pfEaten) {
	*pfEaten = TRUE;
	return S_OK;
}

STDMETHODIMP TextService::OnKeyUp(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pfEaten) {
	return S_OK;
}

STDMETHODIMP TextService::OnPreservedKey(ITfContext *pContext, REFGUID rguid, BOOL *pfEaten) {
	return S_OK;
}


// ITfCompositionSink
STDMETHODIMP TextService::OnCompositionTerminated(TfEditCookie ecWrite, ITfComposition *pComposition) {
	return S_OK;
}


// ITfDisplayAttributeProvider
STDMETHODIMP TextService::EnumDisplayAttributeInfo(IEnumTfDisplayAttributeInfo **ppEnum) {
	return S_OK;
}

STDMETHODIMP TextService::GetDisplayAttributeInfo(REFGUID guidInfo, ITfDisplayAttributeInfo **ppInfo) {
	return S_OK;
}

// edit session handling
STDMETHODIMP TextService::KeyEditSession::DoEditSession(TfEditCookie ec) {
	return textService_->onKeyEditSession(ec, this);
}

// edit session handling
STDMETHODIMP TextService::StartCompositionEditSession::DoEditSession(TfEditCookie ec) {
	return textService_->onStartCompositionEditSession(ec, this);
}

// edit session handling
STDMETHODIMP TextService::EndCompositionEditSession::DoEditSession(TfEditCookie ec) {
	return textService_->onEndCompositionEditSession(ec, this);
}

// callback from edit session of key events
HRESULT TextService::onKeyEditSession(TfEditCookie cookie, KeyEditSession* session) {
	// TODO: perform key handling
	onKeyDown((long)session->wParam_);
	return S_OK;
}

// callback from edit session for starting composition
HRESULT TextService::onStartCompositionEditSession(TfEditCookie cookie, StartCompositionEditSession* session) {
	return S_OK;
}

// callback from edit session for ending composition
HRESULT TextService::onEndCompositionEditSession(TfEditCookie cookie, EndCompositionEditSession* session) {
	return S_OK;
}
