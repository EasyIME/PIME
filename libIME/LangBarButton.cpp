#include "LangBarButton.h"
#include <assert.h>

using namespace Ime;

LangBarButton::LangBarButton(void):
	refCount_(1) {
}

LangBarButton::~LangBarButton(void) {
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
	return S_OK;
}

STDMETHODIMP LangBarButton::GetText(BSTR *pbstrText) {
	return S_OK;
}

// ITfSource
STDMETHODIMP LangBarButton::AdviseSink(REFIID riid, IUnknown *punk, DWORD *pdwCookie) {
	return S_OK;
}

STDMETHODIMP LangBarButton::UnadviseSink(DWORD dwCookie) {
	return S_OK;
}
