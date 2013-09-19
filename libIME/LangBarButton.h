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

	bool enabled() const;
	void setEnabled(bool enable);

	// need to create the button with TF_LBI_STYLE_BTN_TOGGLE style
	bool toggled() const;
	void setToggled(bool toggle);

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
	void update(DWORD flags = TF_LBI_BTNALL);

private:
	int refCount_;
	TextService* textService_;
	TF_LANGBARITEMINFO info_;
	UINT commandId_;
	wchar_t* tooltip_;
	HICON icon_;
	HMENU menu_;
	std::map<DWORD, ITfLangBarItemSink*> sinks_;
	DWORD status_;
};

}

#endif
