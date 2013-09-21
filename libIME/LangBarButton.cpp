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

#include "LangBarButton.h"
#include "TextService.h"
#include "ImeModule.h"
#include <OleCtl.h>
#include <assert.h>
#include <stdlib.h>

namespace Ime {

LangBarButton::LangBarButton(TextService* service, const GUID& guid, UINT commandId, wchar_t* text, DWORD style):
	textService_(service),
	tooltip_(NULL),
	commandId_(commandId),
	menu_(NULL),
	icon_(NULL),
	status_(0),
	refCount_(1) {

	assert(service && service->imeModule());

	textService_->AddRef();

	info_.clsidService = service->imeModule()->textServiceClsid();
	info_.guidItem = guid;
	info_.dwStyle = style;
	info_.ulSort = 0;
	setText(text);
}

LangBarButton::~LangBarButton(void) {
	if(textService_)
		textService_->Release();
	if(menu_)
		::DestroyMenu(menu_);
	if(tooltip_) // allocated by wcsdup()
		::free(tooltip_);
}

const wchar_t* LangBarButton::text() const {
	return info_.szDescription;
}

void LangBarButton::setText(const wchar_t* text) {
	if(text) {
		wcsncpy(info_.szDescription, text, TF_LBI_DESC_MAXLEN - 1);
		info_.szDescription[TF_LBI_DESC_MAXLEN] = 0;
	}
	else
		*info_.szDescription = 0;
	update(TF_LBI_TEXT);
}

void LangBarButton::setText(UINT stringId) {
	const wchar_t* str;
	int len = ::LoadStringW(textService_->imeModule()->hInstance(), stringId, (LPTSTR)&str, 0);
	if(str) {
		if(len > (TF_LBI_DESC_MAXLEN - 1))
			len = TF_LBI_DESC_MAXLEN - 1;
		wcsncpy(info_.szDescription, str, len);
		info_.szDescription[len + 1] = 0;
		update(TF_LBI_TEXT);
	}
}

// public methods
const wchar_t* LangBarButton::tooltip() const {
	return tooltip_;
}

void LangBarButton::setTooltip(const wchar_t* tooltip) {
	if(tooltip_)
		free(tooltip_);
	tooltip_ = _wcsdup(tooltip);
	update(TF_LBI_TOOLTIP);
}

void LangBarButton::setTooltip(UINT tooltipId) {
	const wchar_t* str;
	int len = ::LoadStringW(textService_->imeModule()->hInstance(), tooltipId, (LPTSTR)&str, 0);
	if(str) {
		tooltip_ = (wchar_t*)malloc((len + 1) * sizeof(wchar_t));
		wcsncpy(tooltip_, str, len);
		tooltip_[len] = 0;
		update(TF_LBI_TOOLTIP);
	}
}

HICON LangBarButton::icon() const {
	return icon_;
}

void LangBarButton::setIcon(HICON icon) {
	icon_ = icon;
	update(TF_LBI_ICON);
}

void LangBarButton::setIcon(UINT iconId) {
	HICON icon = ::LoadIconW(textService_->imeModule()->hInstance(), (LPCTSTR)iconId);
	if(icon)
		setIcon(icon);
}

UINT LangBarButton::commandId() const {
	return commandId_;
}

void LangBarButton::setCommandId(UINT id) {
	commandId_ = id;
}

HMENU LangBarButton::menu() const {
	return menu_;
}

void LangBarButton::setMenu(HMENU menu) {
	if(menu_) {
		::DestroyMenu(menu_);
	}
	menu_ = menu;
	// FIXME: how to handle toggle buttons?
	if(menu)
		info_.dwStyle = TF_LBI_STYLE_BTN_MENU;
	else
		info_.dwStyle = TF_LBI_STYLE_BTN_BUTTON;
}

bool LangBarButton::enabled() const {
	return !(status_ & TF_LBI_STATUS_DISABLED);
}

void LangBarButton::setEnabled(bool enable) {
	if(enabled() != enable) {
		if(enable)
			status_ &= ~TF_LBI_STATUS_DISABLED;
		else
			status_ |= TF_LBI_STATUS_DISABLED;
		update(TF_LBI_STATUS);
	}
}

// need to create the button with TF_LBI_STYLE_BTN_TOGGLE style
bool LangBarButton::toggled() const {
	return (status_ & TF_LBI_STATUS_BTN_TOGGLED) ? true : false;
}

void LangBarButton::setToggled(bool toggle) {
	if(toggled() != toggle) {
		if(toggle)
			status_ |= TF_LBI_STATUS_BTN_TOGGLED;
		else
			status_ &= ~TF_LBI_STATUS_BTN_TOGGLED;
		update(TF_LBI_STATUS);
	}
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
	*pdwStatus = status_;
	return S_OK;
}

STDMETHODIMP LangBarButton::Show(BOOL fShow) {
	return E_NOTIMPL;
}

STDMETHODIMP LangBarButton::GetTooltipString(BSTR *pbstrToolTip) {
	if(tooltip_) {
		*pbstrToolTip = ::SysAllocString(tooltip_);
		return *pbstrToolTip ? S_OK : E_FAIL;
	}
	return E_FAIL;
}

// ITfLangBarItemButton
STDMETHODIMP LangBarButton::OnClick(TfLBIClick click, POINT pt, const RECT *prcArea) {
	TextService::CommandType type;
	if(click == TF_LBI_CLK_RIGHT)
		type = TextService::COMMAND_RIGHT_CLICK;
	else
		type = TextService::COMMAND_LEFT_CLICK;
	textService_->onCommand(commandId_, type);
	return S_OK;
}

STDMETHODIMP LangBarButton::InitMenu(ITfMenu *pMenu) {
	if(!menu_)
		return E_FAIL;
	buildITfMenu(pMenu, menu_);
	return S_OK;
}

STDMETHODIMP LangBarButton::OnMenuSelect(UINT wID) {
	textService_->onCommand(wID, TextService::COMMAND_MENU);
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
    if(IsEqualIID(riid, IID_ITfLangBarItemSink)) {
		ITfLangBarItemSink* langBarItemSink;
		if(punk->QueryInterface(IID_ITfLangBarItemSink, (void **)&langBarItemSink) == S_OK) {
		    *pdwCookie = (DWORD)rand();
			sinks_[*pdwCookie] = langBarItemSink;
			return S_OK;
		}
		else
			return E_NOINTERFACE;
	}
    return CONNECT_E_CANNOTCONNECT;
}

STDMETHODIMP LangBarButton::UnadviseSink(DWORD dwCookie) {
	std::map<DWORD, ITfLangBarItemSink*>::iterator it = sinks_.find(dwCookie);
	if(it != sinks_.end()) {
		ITfLangBarItemSink* langBarItemSink = (ITfLangBarItemSink*)it->second;
		langBarItemSink->Release();
		sinks_.erase(it);
		return S_OK;
	}
	return CONNECT_E_NOCONNECTION;
}


// build ITfMenu according to the content of HMENU
void LangBarButton::buildITfMenu(ITfMenu* menu, HMENU templ) {
	int n = ::GetMenuItemCount(templ);
	for(int i = 0; i < n; ++i) {
		MENUITEMINFO mi;
		wchar_t textBuffer[256];
		memset(&mi, 0, sizeof(mi));
		mi.cbSize = sizeof(mi);
		mi.dwTypeData = (LPTSTR)textBuffer;
		mi.cch = 255;
		mi.fMask = MIIM_FTYPE|MIIM_ID|MIIM_STATE|MIIM_STRING|MIIM_SUBMENU;
		if(::GetMenuItemInfoW(templ, i, TRUE, &mi)) {
			UINT flags = 0;
			wchar_t* text;
			ULONG textLen = 0;
			ITfMenu* subMenu = NULL;
			ITfMenu** pSubMenu = NULL;
			if(mi.hSubMenu) { // has submenu
				pSubMenu = &subMenu;
				flags |= TF_LBMENUF_SUBMENU;
			}
			if(mi.fType == MFT_STRING) { // text item
				text = (wchar_t*)mi.dwTypeData;
				textLen = mi.cch;
			}
			else if(mi.fType == MFT_SEPARATOR) { // separator item
				flags |= TF_LBMENUF_SEPARATOR;
			}
			else // other types are not supported
				continue;

			if(mi.fState & MFS_CHECKED) // checked
				flags |= TF_LBMENUF_CHECKED;
			if(mi.fState & (MFS_GRAYED|MFS_DISABLED)) // disabled
				flags |= TF_LBMENUF_GRAYED;
			
			if(menu->AddMenuItem(mi.wID, flags, NULL, 0, text, textLen, pSubMenu) == S_OK) {
				if(subMenu) {
					buildITfMenu(subMenu, mi.hSubMenu);
					subMenu->Release();
				}
			}
		}
		else {
			DWORD error = ::GetLastError();
		}
	}
}

// call all sinks to generate update notifications
void LangBarButton::update(DWORD flags) {
	if(!sinks_.empty()) {
		std::map<DWORD, ITfLangBarItemSink*>::iterator it;
		for(it = sinks_.begin(); it != sinks_.end(); ++it) {
			ITfLangBarItemSink* sink = it->second;
			sink->OnUpdate(flags);
		}
	}
}

} // namespace Ime

