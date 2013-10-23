#pragma once
#ifndef IME_CANDIDATE_LIST_UI_ELEMENT
#define IME_CANDIDATE_LIST_UI_ELEMENT

#include <msctf.h>
#include "ComPtr.h"

namespace Ime {

class CandidateListUIElement:
	public ITfCandidateListUIElement {
public:
	CandidateListUIElement(ITfContext* context);
	virtual ~CandidateListUIElement(void);

	// COM related stuff

    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
    STDMETHODIMP_(ULONG) AddRef(void);
    STDMETHODIMP_(ULONG) Release(void);

	// ITfUIElement
    STDMETHODIMP GetDescription(BSTR *pbstrDescription);
    STDMETHODIMP GetGUID(GUID *pguid);
    STDMETHODIMP Show(BOOL bShow);
    STDMETHODIMP IsShown(BOOL *pbShow);

	// ITfCandidateListUIElement
    STDMETHODIMP GetUpdatedFlags(DWORD *pdwFlags);
    STDMETHODIMP GetDocumentMgr(ITfDocumentMgr **ppdim);
    STDMETHODIMP GetCount(UINT *puCount);
    STDMETHODIMP GetSelection(UINT *puIndex);
    STDMETHODIMP GetString(UINT uIndex, BSTR *pstr);
    STDMETHODIMP GetPageIndex(UINT *pIndex, UINT uSize, UINT *puPageCnt);
    STDMETHODIMP SetPageIndex(UINT *pIndex, UINT uPageCnt);
    STDMETHODIMP GetCurrentPage(UINT *puPage);

private:
	ComPtr<ITfContext> context_;
	int refCount_;
};

}

#endif
