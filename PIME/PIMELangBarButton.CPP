//
//	Copyright (C) 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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


#include "PIMELangBarButton.h"
#include "PIMETextService.h"
#include "libIME/Utils.h"

// this is the GUID of the IME mode icon in Windows 8
// the value is not available in older SDK versions, so let's define it ourselves.
static const GUID _GUID_LBI_INPUTMODE =
{ 0x2C77A81E, 0x41CC, 0x4178,{ 0xA3, 0xA7, 0x5F, 0x8A, 0x98, 0x75, 0x68, 0xE6 } };


namespace PIME {

// static
std::unordered_map<std::wstring, HICON> LangBarButton::iconCache_; // cache loaded icons

LangBarButton::LangBarButton(TextService* service, const std::string& id, const GUID& guid, UINT commandId, const wchar_t* text, DWORD style):
	Ime::LangBarButton(service, guid, commandId, text, style),
	id_(id) {
}

LangBarButton::~LangBarButton() {
}

LangBarButton* LangBarButton::fromJson(TextService* service, rapidjson::Value& info) {
	if (info.IsObject()) {
		std::string id = info["id"].GetString();

		DWORD style = TF_LBI_STYLE_BTN_BUTTON;
		auto prop_it = info.FindMember("style");
		if (prop_it != info.MemberEnd())
			style = prop_it->value.GetUint();

		CLSID guid = { 0 }; // create a new GUID on-the-fly
		if (id == "windows-mode-icon") {
			// Windows 8 systray IME mode icon
			guid = _GUID_LBI_INPUTMODE;
		}
		else {
			CoCreateGuid(&guid);
		}

		LangBarButton* langBtn = new LangBarButton(service, id, guid, 0, NULL, style);
		if (langBtn != nullptr) {
			langBtn->update(info);
			return langBtn;
		}
	}
	return nullptr;
}

void LangBarButton::update(rapidjson::Value& info) {
	auto it = info.FindMember("icon");
	if (it != info.MemberEnd() && it->value.IsString()) {
		std::wstring iconPath = utf8ToUtf16(it->value.GetString());
		HICON icon = NULL;
		auto icon_it = iconCache_.find(iconPath);
		if (icon_it != iconCache_.end()) // found in the cache
			icon = icon_it->second;
		else { // not in the cache
			icon = (HICON)LoadImageW(NULL, iconPath.c_str(), IMAGE_ICON, 0, 0, LR_DEFAULTCOLOR | LR_LOADFROMFILE);
			iconCache_[iconPath] = icon; // cache the icon
		}
		if (icon)
			setIcon(icon);
	}

	it = info.FindMember("commandId");
	if (it != info.MemberEnd() && it->value.IsUint()) {
		UINT cmd = it->value.GetUint();
		setCommandId(cmd);
	}

	it = info.FindMember("text");
	if (it != info.MemberEnd() && it->value.IsString()) {
		std::wstring text = utf8ToUtf16(it->value.GetString());
		setText(text.c_str());
	}

	it = info.FindMember("tooltip");
	if (it != info.MemberEnd() && it->value.IsString()) {
		std::wstring tooltip = utf8ToUtf16(it->value.GetString());
		setTooltip(tooltip.c_str());
	}

	it = info.FindMember("enable");
	if (it != info.MemberEnd() && it->value.IsBool()) {
		bool enable = it->value.GetBool();
		setEnabled(enable);
	}
}


void LangBarButton::clearIconCache() {
	for (auto it = iconCache_.begin(); it != iconCache_.end(); ++it) {
		DestroyIcon(it->second);
	}
	iconCache_.clear();
}

STDMETHODIMP LangBarButton::InitMenu(ITfMenu *pMenu) {
	return Ime::LangBarButton::InitMenu(pMenu);
}

} // namespace PIME
