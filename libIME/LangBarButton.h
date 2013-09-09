#ifndef IME_LANGUAGE_BAR_BUTTON_H
#define IME_LANGUAGE_BAR_BUTTON_H

#include <msctf.h>
#include <string.h>
#include <Windows.h>
#include <map>

namespace Ime {

class TextService;

class LangBarButton:
	public ITfLangBarItemButton,
	public ITfSource {
public:
	LangBarButton(TextService* service, const GUID& guid, UINT commandId = 0, wchar_t* text = NULL, DWORD style = TF_LBI_STYLE_BTN_BUTTON);
	virtual ~LangBarButton(void);

	// public methods
	const wchar_t* text() const;
	void setText(const wchar_t* text);
	void setText(UINT stringId);

	const wchar_t* tooltip() const;
	void setTooltip(const wchar_t* tooltip);
	void setTooltip(UINT stringId);

	HICON icon() const;
	void setIcon(HICON icon);
	void setIcon(UINT iconId);

	UINT commandId() const;
	void setCommandId(UINT id);

	HMENU menu() const;
	void setMenu(HMENU menu);

	// COM-related stuff

	// IUnknown
	STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
	STDMETHODIMP_(ULONG) AddRef(void);
	STDMETHODIMP_(ULONG) Release(void);

	// ITfLangBarItem
	STDMETHODIMP GetInfo(TF_LANGBARITEMINFO *pInfo);
	STDMETHODIMP GetStatus(DWORD *pdwStatus);
	STDMETHODIMP Show(BOOL fShow);
	STDMETHODIMP GetTooltipString(BSTR *pbstrToolTip);

	// ITfLangBarItemButton
	STDMETHODIMP OnClick(TfLBIClick click, POINT pt, const RECT *prcArea);
	STDMETHODIMP InitMenu(ITfMenu *pMenu);
	STDMETHODIMP OnMenuSelect(UINT wID);
	STDMETHODIMP GetIcon(HICON *phIcon);
	STDMETHODIMP GetText(BSTR *pbstrText);

	// ITfSource
	STDMETHODIMP AdviseSink(REFIID riid, IUnknown *punk, DWORD *pdwCookie);
	STDMETHODIMP UnadviseSink(DWORD dwCookie);

private:
	void buildITfMenu(ITfMenu* menu, HMENU templ);

private:
	int refCount_;
	TextService* textService_;
	TF_LANGBARITEMINFO info_;
	UINT commandId_;
	wchar_t* tooltip_;
	HICON icon_;
	HMENU menu_;
	std::map<DWORD, ITfLangBarItemSink*> sinks_;
};

}

#endif
