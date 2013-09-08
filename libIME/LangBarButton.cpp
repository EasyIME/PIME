#include "LangBarButton.h"
#include "TextService.h"
#include "ImeModule.h"
#include <assert.h>

using namespace Ime;

LangBarButton::LangBarButton(TextService* service, const GUID& guid, wchar_t* text, DWORD style):
	textService_(service),
	tooltip_(NULL),
	refCount_(1) {

	assert(service && service->module());

	textService_->AddRef();

	info_.clsidService = service->module()->textServiceClsid();
	info_.guidItem = guid;
	info_.dwStyle = style;
	info_.ulSort = 0;
	setText(text);
}

LangBarButton::~LangBarButton(void) {
	if(textService_)
		textService_->Release();
	if(tooltip_) // allocated by wcsdup()
		::free(tooltip_);
}

const wchar_t* LangBarButton::text() const {
	return info_.szDescription;
}

void LangBarButton::setText(wchar_t* text) {
	if(text) {
		wcsncpy(info_.szDescription, text, TF_LBI_DESC_MAXLEN - 1);
	}
	else
		*info_.szDescription = 0;
	// FIXME: do we need to inform TSF to update the UI?
}

// public methods
const wchar_t* LangBarButton::tooltip() const {
	return tooltip_;
}

void LangBarButton::setTooltip(const wchar_t* tooltip) {
	if(tooltip_)
		free(tooltip_);
	tooltip = _wcsdup(tooltip);
	// FIXME: do we need to inform TSF to update the UI?
}


HICON LangBarButton::icon() const {
	return icon_;
}

void LangBarButton::setIcon(HICON icon) {
	icon_ = icon;
}

// COM stuff

// IUnknown
STDMETHODIMP LangBarButton::QueryInterface(REFIID riid, void **ppvObj) {
    if (ppvObj == NULL)
        return E_INVALIDARG;

	if(IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_ITfLangBarItem) || IsEqualIID(riid, IID_ITfLangBarItemButton))
		*ppvObj = (ITfLangBarItemButton*)this;
	else if(IsEqualIID(riid, IID_ITfSource))
		*ppvObj = (ITfSource*)this;
	else
		*ppvObj = NULL;

	if(*ppvObj) {
		AddRef();
		return S_OK;
	}
	return E_NOINTERFACE;
}

// IUnknown implementation
STDMETHODIMP_(ULONG) LangBarButton::AddRef(void) {
	return ++refCount_;
}

STDMETHODIMP_(ULONG) LangBarButton::Release(void) {
	assert(refCount_ > 0);
	--refCount_;
	if(0 == refCount_)
		delete this;
	return refCount_;
}

// ITfLangBarItem
STDMETHODIMP LangBarButton::GetInfo(TF_LANGBARITEMINFO *pInfo) {
	*pInfo = info_;
	return S_OK;
}

STDMETHODIMP LangBarButton::GetStatus(DWORD *pdwStatus) {
	*pdwStatus = 0;
	return S_OK;
}

STDMETHODIMP LangBarButton::Show(BOOL fShow) {
	return E_NOTIMPL;
}

STDMETHODIMP LangBarButton::GetTooltipString(BSTR *pbstrToolTip) {
	return S_OK;
}

// ITfLangBarItemButton
STDMETHODIMP LangBarButton::OnClick(TfLBIClick click, POINT pt, const RECT *prcArea) {
	return S_OK;
}

STDMETHODIMP LangBarButton::InitMenu(ITfMenu *pMenu) {
	return S_OK;
}

STDMETHODIMP LangBarButton::OnMenuSelect(UINT wID) {
	return S_OK;
}

STDMETHODIMP LangBarButton::GetIcon(HICON *phIcon) {
	*phIcon = icon_;
	return S_OK;
}

STDMETHODIMP LangBarButton::GetText(BSTR *pbstrText) {
	*pbstrText = ::SysAllocString(info_.szDescription);
	return *pbstrText ? S_OK : S_FALSE;
}

// ITfSource
STDMETHODIMP LangBarButton::AdviseSink(REFIID riid, IUnknown *punk, DWORD *pdwCookie) {
	return S_OK;
}

STDMETHODIMP LangBarButton::UnadviseSink(DWORD dwCookie) {
	return S_OK;
}

