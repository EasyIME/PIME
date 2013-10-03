#include "CandidateListUIElement.h"
#include <assert.h>

namespace Ime {

CandidateListUIElement::CandidateListUIElement(ITfContext* context):
	context_(context),
	refCount_(1) {
}

CandidateListUIElement::~CandidateListUIElement(void) {
}

// COM stuff

// IUnknown
STDMETHODIMP CandidateListUIElement::QueryInterface(REFIID riid, void **ppvObj) {
    if (ppvObj == NULL)
        return E_INVALIDARG;

	if(IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_ITfCandidateListUIElement))
		*ppvObj = (ITfCandidateListUIElement*)this;
	else
		*ppvObj = NULL;

	if(*ppvObj) {
		AddRef();
		return S_OK;
	}
	return E_NOINTERFACE;
}

STDMETHODIMP_(ULONG) CandidateListUIElement::AddRef(void) {
	return ++refCount_;
}

STDMETHODIMP_(ULONG) CandidateListUIElement::Release(void) {
	assert(refCount_ > 0);
	--refCount_;
	if(0 == refCount_)
		delete this;
	return refCount_;
}

// ITfUIElement
STDMETHODIMP CandidateListUIElement::GetDescription(BSTR *pbstrDescription) {
	return S_OK;
}

STDMETHODIMP CandidateListUIElement::GetGUID(GUID *pguid) {
	return S_OK;
}

STDMETHODIMP CandidateListUIElement::Show(BOOL bShow) {
	return S_OK;
}

STDMETHODIMP CandidateListUIElement::IsShown(BOOL *pbShow) {
	return S_OK;
}

// ITfCandidateListUIElement
STDMETHODIMP CandidateListUIElement::GetUpdatedFlags(DWORD *pdwFlags) {
	return S_OK;
}

STDMETHODIMP CandidateListUIElement::GetDocumentMgr(ITfDocumentMgr **ppdim) {
	if(!context_)
		return E_FAIL;
	return context_->GetDocumentMgr(ppdim);
}

STDMETHODIMP CandidateListUIElement::GetCount(UINT *puCount) {
	return S_OK;
}

STDMETHODIMP CandidateListUIElement::GetSelection(UINT *puIndex) {
	return S_OK;
}

STDMETHODIMP CandidateListUIElement::GetString(UINT uIndex, BSTR *pstr) {
	return S_OK;
}

STDMETHODIMP CandidateListUIElement::GetPageIndex(UINT *pIndex, UINT uSize, UINT *puPageCnt) {
	return S_OK;
}

STDMETHODIMP CandidateListUIElement::SetPageIndex(UINT *pIndex, UINT uPageCnt) {
	return S_OK;
}

STDMETHODIMP CandidateListUIElement::GetCurrentPage(UINT *puPage) {
	return S_OK;
}

}
