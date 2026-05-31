//
//	Copyright (C) 2015 - 2020 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

#include "PIMEClient.h"
#include "libIME2/src/Utils.h"
#include <algorithm>
#include <nlohmann/json.hpp>

#include "PIMETextService.h"
#include <VersionHelpers.h> // Provided by Windows SDK >= 8.1
#include <Winnls.h> // for IS_HIGH_SURROGATE() macro for checking UTF16 surrogate pairs
#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <memory>

using namespace std;
using json = nlohmann::json;

namespace PIME {

static constexpr const char* kDayiProfileGuid = "{e6943374-70f5-4540-aa0f-3205c7dcca84}";
static constexpr const char* kChewingProfileGuid = "{f80736aa-28db-423a-92c9-5540f501c939}";
static constexpr const char* kChecjProfileGuid = "{f828d2dc-81be-466e-9cfe-24bb03172693}";
static constexpr const char* kCheliuProfileGuid = "{72844b94-5908-4674-8626-4353755bc5db}";

static std::string uuidToString(const UUID& uuid) {
	std::string result;
	LPOLESTR buf = nullptr;
	if (SUCCEEDED(::StringFromCLSID(uuid, &buf))) {
		result = utf16ToUtf8(buf);
		::CoTaskMemFree(buf);
		// convert GUID to lwoer case
		transform(result.begin(), result.end(), result.begin(), tolower);
	}
	return result;
}

bool uuidFromString(const char* uuidStr, UUID& result) {
	std::wstring utf16UuidStr = utf8ToUtf16(uuidStr);
	return SUCCEEDED(CLSIDFromString(utf16UuidStr.c_str(), &result));
}

static bool parseHexColor(const json& value, COLORREF& color) {
	if (!value.is_string())
		return false;
	std::string text = value.get<std::string>();
	if (text.size() != 7 || text[0] != '#')
		return false;
	char* end = nullptr;
	unsigned long rgb = std::strtoul(text.c_str() + 1, &end, 16);
	if (end == nullptr || *end != '\0')
		return false;
	color = RGB((rgb >> 16) & 0xff, (rgb >> 8) & 0xff, rgb & 0xff);
	return true;
}

static void parseHexColorMember(const json& object, const char* name, COLORREF& color) {
	auto it = object.find(name);
	if (it != object.end())
		parseHexColor(*it, color);
}

static std::string normalizedThemeName(const std::string& theme) {
	std::string normalized;
	for (unsigned char ch : theme) {
		if (std::isalnum(ch))
			normalized.push_back((char)std::tolower(ch));
	}
	return normalized;
}

static int candidateKeyStyleValue(const std::string& style) {
	const std::string name = normalizedThemeName(style);
	if (name == "divider" || name == "dividerslim")
		return Ime::CandidateWindow::KeyStyleDivider;
	if (name == "quiet" || name == "quietkey")
		return Ime::CandidateWindow::KeyStyleQuiet;
	if (name == "badge" || name == "badgeminimal")
		return Ime::CandidateWindow::KeyStyleBadgeMinimal;
	if (name == "accentdot")
		return Ime::CandidateWindow::KeyStyleAccentDot;
	if (name == "rail" || name == "railmarker")
		return Ime::CandidateWindow::KeyStyleRail;
	if (name == "monospace" || name == "monospaceslot")
		return Ime::CandidateWindow::KeyStyleMonospaceSlot;
	if (name == "wordfirst")
		return Ime::CandidateWindow::KeyStyleWordFirst;
	if (name == "softcapsule")
		return Ime::CandidateWindow::KeyStyleSoftCapsule;
	if (name == "lefttag")
		return Ime::CandidateWindow::KeyStyleLeftTag;
	if (name == "glow" || name == "glowkey")
		return Ime::CandidateWindow::KeyStyleGlowKey;
	if (name == "microtab")
		return Ime::CandidateWindow::KeyStyleMicroTab;
	if (name == "wordanchor" || name == "underline" || name == "rule" || name == "rulekey")
		return Ime::CandidateWindow::KeyStyleWordAnchor;
	return Ime::CandidateWindow::KeyStyleKeycap;
}

static int candidateMessageStyleValue(const std::string& style) {
	const std::string name = normalizedThemeName(style);
	if (name == "bar")
		return Ime::CandidateWindow::MessageStyleBar;
	if (name == "dot")
		return Ime::CandidateWindow::MessageStyleDot;
	return Ime::CandidateWindow::MessageStyleBadge;
}

static void candidateThemeColors(const std::string& theme,
	COLORREF& panelBackground,
	COLORREF& panelBorder,
	COLORREF& textPrimary,
	COLORREF& textSecondary,
	COLORREF& highlightBackground,
	COLORREF& highlightBorder,
	COLORREF& highlightText) {
	const std::string name = normalizedThemeName(theme);
	if (name == "nightcomfort" || name == "night" || name == "dark") {
		panelBackground = RGB(27, 28, 32);
		panelBorder = RGB(74, 77, 87);
		textPrimary = RGB(229, 232, 238);
		textSecondary = RGB(169, 175, 186);
		highlightBackground = RGB(64, 95, 138);
		highlightBorder = RGB(94, 126, 167);
		highlightText = RGB(238, 244, 255);
	}
	else if (name == "softfocus" || name == "soft") {
		panelBackground = RGB(25, 29, 33);
		panelBorder = RGB(68, 82, 90);
		textPrimary = RGB(228, 235, 238);
		textSecondary = RGB(168, 181, 186);
		highlightBackground = RGB(63, 111, 107);
		highlightBorder = RGB(106, 153, 147);
		highlightText = RGB(236, 251, 248);
	}
	else if (name == "warmgray" || name == "warmgrey") {
		panelBackground = RGB(32, 32, 29);
		panelBorder = RGB(88, 85, 75);
		textPrimary = RGB(235, 231, 220);
		textSecondary = RGB(183, 177, 163);
		highlightBackground = RGB(95, 104, 77);
		highlightBorder = RGB(135, 147, 111);
		highlightText = RGB(247, 243, 231);
	}
	else if (name == "graphite") {
		panelBackground = RGB(18, 20, 26);
		panelBorder = RGB(68, 74, 87);
		textPrimary = RGB(243, 245, 250);
		textSecondary = RGB(174, 181, 196);
		highlightBackground = RGB(65, 105, 215);
		highlightBorder = RGB(111, 146, 235);
		highlightText = RGB(237, 243, 255);
	}
	else if (name == "slateteal" || name == "teal") {
		panelBackground = RGB(21, 32, 39);
		panelBorder = RGB(63, 90, 100);
		textPrimary = RGB(240, 248, 251);
		textSecondary = RGB(165, 186, 194);
		highlightBackground = RGB(47, 127, 159);
		highlightBorder = RGB(96, 173, 200);
		highlightText = RGB(233, 251, 255);
	}
	else if (name == "olive") {
		panelBackground = RGB(23, 27, 22);
		panelBorder = RGB(75, 89, 65);
		textPrimary = RGB(244, 247, 239);
		textSecondary = RGB(180, 189, 167);
		highlightBackground = RGB(93, 127, 54);
		highlightBorder = RGB(145, 185, 98);
		highlightText = RGB(244, 255, 232);
	}
	else if (name == "plum") {
		panelBackground = RGB(29, 23, 33);
		panelBorder = RGB(96, 75, 102);
		textPrimary = RGB(251, 244, 255);
		textSecondary = RGB(192, 173, 202);
		highlightBackground = RGB(122, 85, 184);
		highlightBorder = RGB(170, 131, 230);
		highlightText = RGB(251, 243, 255);
	}
	else if (name == "amber") {
		panelBackground = RGB(33, 26, 18);
		panelBorder = RGB(104, 83, 58);
		textPrimary = RGB(255, 248, 237);
		textSecondary = RGB(207, 189, 164);
		highlightBackground = RGB(154, 103, 48);
		highlightBorder = RGB(213, 154, 88);
		highlightText = RGB(255, 243, 222);
	}
	else if (name == "paper") {
		panelBackground = RGB(251, 250, 246);
		panelBorder = RGB(183, 172, 156);
		textPrimary = RGB(39, 33, 25);
		textSecondary = RGB(120, 107, 93);
		highlightBackground = RGB(49, 95, 135);
		highlightBorder = RGB(36, 73, 103);
		highlightText = RGB(247, 251, 255);
	}
	else if (name == "mistlight" || name == "mist") {
		panelBackground = RGB(233, 237, 240);
		panelBorder = RGB(168, 179, 188);
		textPrimary = RGB(36, 48, 58);
		textSecondary = RGB(102, 114, 125);
		highlightBackground = RGB(95, 127, 148);
		highlightBorder = RGB(75, 104, 123);
		highlightText = RGB(247, 251, 253);
	}
	else if (name == "sepiadim" || name == "sepia") {
		panelBackground = RGB(40, 37, 31);
		panelBorder = RGB(93, 86, 74);
		textPrimary = RGB(235, 226, 211);
		textSecondary = RGB(185, 173, 154);
		highlightBackground = RGB(109, 101, 71);
		highlightBorder = RGB(149, 138, 99);
		highlightText = RGB(248, 239, 217);
	}
	else {
		panelBackground = RGB(247, 249, 252);
		panelBorder = RGB(174, 184, 203);
		textPrimary = RGB(24, 34, 53);
		textSecondary = RGB(101, 113, 135);
		highlightBackground = RGB(47, 110, 234);
		highlightBorder = RGB(29, 86, 196);
		highlightText = RGB(255, 255, 255);
	}
}

static bool usesModernCandidateDefault(const std::string& guid) {
	return guid == kDayiProfileGuid ||
		guid == kChewingProfileGuid ||
		guid == kChecjProfileGuid ||
		guid == kCheliuProfileGuid;
}

static bool shouldHoldKeyWhenBackendUnavailable(const std::string& guid, Ime::KeyEvent& keyEvent) {
	if (!usesModernCandidateDefault(guid))
		return false;

	if (keyEvent.isKeyDown(VK_CONTROL) || keyEvent.isKeyDown(VK_MENU))
		return false;

	return keyEvent.charCode() >= 0x20;
}

Client::Client(TextService* service, REFIID langProfileGuid):
	textService_(service),
	pipe_(INVALID_HANDLE_VALUE),
	nextSeqNum_(0),
	isActivated_(false),
	guid_{ uuidToString(langProfileGuid) },
	shouldWaitConnection_{ true },
	ioEvent_{ CreateEvent(NULL, TRUE, FALSE, NULL) } {
	if (usesModernCandidateDefault(guid_)) {
		textService_->setCandPerRow(6);
		textService_->setCandidateEdgeAvoidance(true);
		textService_->setCandidateTheme(
			RGB(27, 28, 32),
			RGB(74, 77, 87),
			RGB(229, 232, 238),
			RGB(169, 175, 186),
			RGB(64, 95, 138),
			RGB(94, 126, 167),
			RGB(238, 244, 255));
		textService_->setCandidateSpacing(6, 4, 6);
		textService_->setCandidateStableWidth(true, 286);
		textService_->setCandidateMaxWidth(true, 300);
		textService_->setCandidateModernStyle(true);
	}
}

Client::~Client(void) {
	closeRpcConnection();
	resetTextServiceState();
	LangBarButton::clearIconCache();
}

// pack a keyEvent object into a json value
//static
void Client::addKeyEventToRpcRequest(json& request, Ime::KeyEvent& keyEvent) {
	request["charCode"] = keyEvent.charCode();
	request["keyCode"] = keyEvent.keyCode();
	request["repeatCount"] = keyEvent.repeatCount();
	request["scanCode"] = keyEvent.scanCode();
	request["isExtended"] = keyEvent.isExtended();
	json keyStates = json::array();
	const BYTE* states = keyEvent.keyStates();
	for (int i = 0; i < 256; ++i) {
		keyStates.push_back(states[i]);
	}
	request["keyStates"] = keyStates;
}

bool Client::handleRpcResponse(json& msg, Ime::EditSession* session) {
	bool success = msg.value("success", false);
	if (success) {
		updateStatus(msg, session);
	}
	return success;
}

void Client::updateUI(json& data) {
	bool pendingModernStyle = false;
	bool hasModernStyle = false;

	for (auto it = data.begin(); it != data.end(); ++it) {
		const std::string& name = it.key();
		const json& value = it.value();
		if (value.is_string() && name == "candFontName") {
			wstring fontName = utf8ToUtf16(value.get<string>().c_str());
			textService_->setCandFontName(fontName);
		}
		else if (value.is_number_integer() && name == "candFontSize") {
			textService_->setCandFontSize(value.get<int>());
		}
		else if (value.is_number_integer() && name == "candPerRow") {
			textService_->setCandPerRow(value.get<int>());
		}
		else if (value.is_boolean() && name == "candUseCursor") {
			textService_->setCandUseCursor(value.get<bool>());
		}
		else if (value.is_boolean() && name == "candidateModernStyle") {
			// Defer until theme/spacing are applied so applyCandidateWindowStyle()
			// runs once with the final state instead of triggering early with stale colors.
			pendingModernStyle = value.get<bool>();
			hasModernStyle = true;
		}
		else if (value.is_boolean() && name == "candidateEdgeAvoidance") {
			textService_->setCandidateEdgeAvoidance(value.get<bool>());
		}
		else if (value.is_string() && name == "candidateKeyStyle") {
			textService_->setCandidateKeyStyle(candidateKeyStyleValue(value.get<string>()));
		}
		else if (value.is_string() && name == "candidateMessageStyle") {
			textService_->setCandidateMessageStyle(candidateMessageStyleValue(value.get<string>()));
		}
	}

	// Apply theme colors (preset) with optional per-key overrides from candidateColors
	auto themeIt = data.find("candidateTheme");
	auto colorsIt = data.find("candidateColors");
	if ((themeIt != data.end() && themeIt->is_string()) ||
	    (colorsIt != data.end() && colorsIt->is_object())) {
		COLORREF panelBg, panelBorder, textPrimary, textSecondary, highlightBg, highlightBorder, highlightText;
		std::string theme = (themeIt != data.end() && themeIt->is_string()) ? themeIt->get<std::string>() : "light";
		candidateThemeColors(theme, panelBg, panelBorder, textPrimary, textSecondary, highlightBg, highlightBorder, highlightText);
		if (colorsIt != data.end() && colorsIt->is_object()) {
			parseHexColorMember(*colorsIt, "panelBackground", panelBg);
			parseHexColorMember(*colorsIt, "panelBorder", panelBorder);
			parseHexColorMember(*colorsIt, "textPrimary", textPrimary);
			parseHexColorMember(*colorsIt, "textSecondary", textSecondary);
			parseHexColorMember(*colorsIt, "highlightBackground", highlightBg);
			parseHexColorMember(*colorsIt, "highlightBorder", highlightBorder);
			parseHexColorMember(*colorsIt, "highlightText", highlightText);
		}
		textService_->setCandidateTheme(panelBg, panelBorder, textPrimary, textSecondary, highlightBg, highlightBorder, highlightText);
	}

	// Apply spacing style
	auto styleIt = data.find("candidateStyle");
	if (styleIt != data.end() && styleIt->is_object()) {
		int contentMargin = styleIt->value("contentMargin", 8);
		int textMargin = styleIt->value("textMargin", 6);
		int borderRadius = styleIt->value("borderRadius", 8);
		textService_->setCandidateSpacing(contentMargin, textMargin, borderRadius);
	}

	auto stableIt = data.find("candidateStableWidth");
	auto minWidthIt = data.find("candidateMinWidth");
	if ((stableIt != data.end() && stableIt->is_boolean()) ||
	    (minWidthIt != data.end() && minWidthIt->is_number_integer())) {
		bool stableWidth = stableIt != data.end() && stableIt->is_boolean() ? stableIt->get<bool>() : false;
		int minWidth = minWidthIt != data.end() && minWidthIt->is_number_integer() ? minWidthIt->get<int>() : 0;
		textService_->setCandidateStableWidth(stableWidth, minWidth);
	}

	auto wrapIt = data.find("candidateWrapToMaxWidth");
	auto maxWidthIt = data.find("candidateMaxWidth");
	if ((wrapIt != data.end() && wrapIt->is_boolean()) ||
	    (maxWidthIt != data.end() && maxWidthIt->is_number_integer())) {
		bool wrapToMaxWidth = wrapIt != data.end() && wrapIt->is_boolean() ? wrapIt->get<bool>() : false;
		int maxWidth = maxWidthIt != data.end() && maxWidthIt->is_number_integer() ? maxWidthIt->get<int>() : 0;
		textService_->setCandidateMaxWidth(wrapToMaxWidth, maxWidth);
	}

	// Apply modernStyle last: triggers the final applyCandidateWindowStyle() with
	// theme and spacing already in their new state.
	if (hasModernStyle) {
		textService_->setCandidateModernStyle(pendingModernStyle);
	}
}

void Client::updateSelectionKeys(json& msg) {
	// set sel keys before update candidates
	auto& setSelKeysVal = msg["setSelKeys"];
	if (setSelKeysVal.is_string()) {
		// keys used to select candidates
		std::wstring selKeys = utf8ToUtf16(setSelKeysVal.get<string>().c_str());
		textService_->setSelKeys(selKeys);
	}
}

void Client::updateMessageWindow(json& msg, Ime::EditSession* session, bool& endComposition) {
	auto& showMessageVal = msg["showMessage"];
	if (showMessageVal.is_object()) {
		auto& message = showMessageVal["message"];
		auto& duration = showMessageVal["duration"];
		if (message.is_string() && duration.is_number_integer()) {
			if (textService_->candidateModernStyle()) {
				textService_->hideMessage();
				msg["candidateMessage"] = message.get<string>();
				msg["showCandidates"] = true;
				return;
			}
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
				endComposition = true;
			}
			textService_->showMessage(session, utf8ToUtf16(message.get<string>().c_str()), duration.get<int>());
		}
	}

	// hide message
	auto& hideMessageVal = msg["hideMessage"];
	if (hideMessageVal.is_boolean() && hideMessageVal.get<bool>()) {
		textService_->hideMessage();
	}
}

void Client::updateCommitString(json& msg, Ime::EditSession* session) {
	// handle comosition and commit strings
	auto& commitStringVal = msg["commitString"];
	if (commitStringVal.is_string()) {
		std::wstring commitString = utf8ToUtf16(commitStringVal.get<string>().c_str());
		if (!commitString.empty()) {
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
			}
			textService_->setCompositionString(session, commitString.c_str(), commitString.length());
			// FIXME: update the position of candidate and message window when the composition string is changed.
			if (textService_->candidateWindow_ != nullptr) {
				textService_->updateCandidatesWindow(session);
			}
			if (textService_->messageWindow_ != nullptr) {
				textService_->updateMessageWindow(session);
			}
			textService_->endComposition(session->context());
		}
	}
}

void Client::updateComposition(json& msg, Ime::EditSession* session, bool& endComposition) {
	auto& compositionStringVal = msg["compositionString"];
	bool emptyComposition = false;
	bool hasCompositionString = false;
	std::wstring compositionString;
	if (compositionStringVal.is_string()) {
		// composition buffer
		compositionString = utf8ToUtf16(compositionStringVal.get<string>().c_str());
		hasCompositionString = true;
		if (compositionString.empty()) {
			emptyComposition = true;
			if (textService_->isComposing()) {
				textService_->setCompositionString(session, L"", 0);
			}
			if (textService_->isComposing() && !textService_->showingCandidates()) {
				// when the composition buffer is empty and we are not showing the candidate list, end composition.
				endComposition = true;
			}
		}
		else {
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
			}
			textService_->setCompositionString(session, compositionString.c_str(), compositionString.length());
		}
		// FIXME: update the position of candidate and message window when the composition string is changed.
		if (textService_->candidateWindow_ != nullptr) {
			textService_->updateCandidatesWindow(session);
		}
		if (textService_->messageWindow_ != nullptr) {
			textService_->updateMessageWindow(session);
		}
	}

	auto& compositionCursorVal = msg["compositionCursor"];
	if (compositionCursorVal.is_number_integer()) {
		// composition cursor
		if (!emptyComposition) {
			int compositionCursor = compositionCursorVal.get<int>();
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
			}
			// NOTE:
			// This fixes PIME bug #166: incorrect handling of UTF-16 surrogate pairs.
			// The TSF API unfortunately treat a UTF-16 surrogate pair as two characters while
			// they actually represent one unicode character only. To workaround this TSF bug,
			// we get the composition string, and try to move the cursor twice when a UTF-16
			// surrogate pair is found.
			if (!hasCompositionString)
				compositionString = textService_->compositionString(session);
			int fixedCursorPos = 0;
			for (int i = 0; i < compositionCursor; ++i) {
				++fixedCursorPos;
				if (IS_HIGH_SURROGATE(compositionString[i])) // this is the first part of a UTF16 surrogate pair (Windows uses UTF16-LE)
					++fixedCursorPos;
			}
			textService_->setCompositionCursor(session, fixedCursorPos);
		}
	}
	if (endComposition) {
		textService_->endComposition(session->context());
	}
}

void Client::updateLanguageButtons(json& msg) {
	// language buttons
	auto& addButtonVal = msg["addButton"];
	if (addButtonVal.is_array()) {
		for (auto& btn : addButtonVal) {
			// FIXME: when to clear the id <=> button map??
			auto langBtn = Ime::ComPtr<PIME::LangBarButton>::takeover(PIME::LangBarButton::fromJson(textService_, btn));
			if (langBtn != nullptr) {
				buttons_.emplace(langBtn->id(), langBtn); // insert into the map
				textService_->addButton(langBtn);
			}
		}
	}

	const auto& removeButtonVal = msg["removeButton"];
	if (removeButtonVal.is_array()) {
		// FIXME: handle windows-mode-icon
		for (const auto& btn : removeButtonVal) {
			if (btn.is_string()) {
				string id = btn.get<string>();
				auto map_it = buttons_.find(id);
				if (map_it != buttons_.end()) {
					textService_->removeButton(map_it->second);
					buttons_.erase(map_it); // remove from the map
				}
			}
		}
	}
	auto& changeButtonVal = msg["changeButton"];
	if (changeButtonVal.is_array()) {
		// FIXME: handle windows-mode-icon
		for (auto& btn : changeButtonVal) {
			if (btn.is_object()) {
				string id = btn["id"].get<string>();
				auto map_it = buttons_.find(id);
				if (map_it != buttons_.end()) {
					map_it->second->updateFromJson(btn);
				}
			}
		}
	}
}

void Client::updatePreservedKeys(json& msg) {
	auto& addPreservedKeyVal = msg["addPreservedKey"];
	if (addPreservedKeyVal.is_array()) {
		// preserved keys
		for (auto& key : addPreservedKeyVal) {
			if (key.is_object()) {
				UINT keyCode = key["keyCode"].get<unsigned int>();
				UINT modifiers = key["modifiers"].get<unsigned int>();
				UUID guid = { 0 };
				if (uuidFromString(key["guid"].get<string>().c_str(), guid)) {
					textService_->addPreservedKey(keyCode, modifiers, guid);
				}
			}
		}
	}

	const auto& removePreservedKeyVal = msg["removePreservedKey"];
	if (removePreservedKeyVal.is_array()) {
		for (auto& item : removePreservedKeyVal) {
			if (item.is_string()) {
				UUID guid = { 0 };
				if (uuidFromString(item.get<string>().c_str(), guid)) {
					textService_->removePreservedKey(guid);
				}
			}
		}
	}
}

void Client::updateKeyboardStatus(json& msg) {
	const auto& openKeyboardVal = msg["openKeyboard"];
	if (openKeyboardVal.is_boolean()) {
		textService_->setKeyboardOpen(openKeyboardVal.get<bool>());
	}
}

void Client::updateStatus(json& msg, Ime::EditSession* session) {
	// We need to handle ordering of some types of the requests.
	// For example, setCompositionCursor() should happen after setCompositionCursor().
	// UI customization must be applied before candidateList creates or refreshes
	// the candidate window; otherwise the first rendered window keeps the old UI.
	auto& customizeUIVal = msg["customizeUI"];
	if (customizeUIVal.is_object()) {
		updateUI(customizeUIVal);
	}

	updateSelectionKeys(msg);

	// show message
	bool endComposition = false;
	updateMessageWindow(msg, session, endComposition);

	if (session != nullptr) { // if an edit session is available
		updateCandidateList(msg, session);

		updateCommitString(msg, session);

		updateComposition(msg, session, endComposition);

	}

	updateLanguageButtons(msg);

	// preserved keys
	updatePreservedKeys(msg);

	// keyboard status
	updateKeyboardStatus(msg);
}

void Client::updateCandidateList(json& msg, Ime::EditSession* session) {
	// handle candidate list
	const auto& showCandidatesVal = msg["showCandidates"];
	const auto& candidateMessageVal = msg["candidateMessage"];
	const auto& candidateMessageStyleVal = msg["candidateMessageStyle"];
	bool hasCandidateMessage = false;
	if (candidateMessageVal.is_string()) {
		std::wstring message = utf8ToUtf16(candidateMessageVal.get<std::string>().c_str());
		hasCandidateMessage = !message.empty();
		if (candidateMessageStyleVal.is_string()) {
			textService_->setCandidateMessageDisplayStyle(candidateMessageStyleValue(candidateMessageStyleVal.get<std::string>()));
		}
		else {
			textService_->resetCandidateMessageDisplayStyle();
		}
		textService_->setCandidateMessage(message);
	}
	else if (showCandidatesVal.is_boolean()) {
		textService_->resetCandidateMessageDisplayStyle();
		textService_->setCandidateMessage(L"");
	}

	if (showCandidatesVal.is_boolean()) {
		if (showCandidatesVal.get<bool>() || hasCandidateMessage) {
			// start composition if we are not composing.
			// this is required to get correctly position the candidate window
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
			}
			textService_->showCandidates(session);
		}
		else {
			textService_->setCandidateMessage(L"");
			textService_->hideCandidates();
		}
	}
	else if (hasCandidateMessage) {
		if (!textService_->isComposing()) {
			textService_->startComposition(session->context());
		}
		textService_->showCandidates(session);
	}

	// parse candidateHeader before candidateList so candidateHeader_ is correct
	// when updateCandidates() calls setHeader(candidateHeader_)
	const auto& candidateHeaderVal = msg["candidateHeader"];
	if (candidateHeaderVal.is_string()) {
		std::wstring header = utf8ToUtf16(candidateHeaderVal.get<std::string>().c_str());
		textService_->setCandidateHeader(header);
	}
	else if (showCandidatesVal.is_boolean() && !showCandidatesVal.get<bool>() && !hasCandidateMessage) {
		textService_->setCandidateHeader(L"");
	}

	const auto& candidatePageInfoVal = msg["candidatePageInfo"];
	if (candidatePageInfoVal.is_string()) {
		std::wstring info = utf8ToUtf16(candidatePageInfoVal.get<std::string>().c_str());
		textService_->setCandidatePageInfo(info);
	}
	else if (showCandidatesVal.is_boolean() && !showCandidatesVal.get<bool>() && !hasCandidateMessage) {
		textService_->setCandidatePageInfo(L"");
	}

	const auto& candidateListVal = msg["candidateList"];
	if (candidateListVal.is_array()) {
		if (!hasCandidateMessage) {
			textService_->setCandidateMessage(L"");
		}
		// handle candidates
		// FIXME: directly access private member is dirty!!!
		vector<wstring>& candidates = textService_->candidates_;
		candidates.clear();
		for (const auto& candidate : candidateListVal) {
			if (candidate.is_string()) {
				candidates.emplace_back(utf8ToUtf16(candidate.get<string>().c_str()));
			}
		}
		textService_->updateCandidates(session);
		if (showCandidatesVal.is_boolean() && !showCandidatesVal.get<bool>() && !hasCandidateMessage) {
			textService_->hideCandidates();
		}
	}
	else if (hasCandidateMessage) {
		textService_->candidates_.clear();
		textService_->updateCandidates(session);
	}

	const auto& candidateCursorVal = msg["candidateCursor"];
	if (candidateCursorVal.is_number_integer()) {
		if (textService_->candidateWindow_ != nullptr) {
			textService_->candidateWindow_->setCurrentSel(candidateCursorVal.get<int>());
			textService_->refreshCandidates();
		}
	}
}

// handlers for the text service
void Client::onActivate() {
	json req = createRpcRequest("onActivate");
	req["isKeyboardOpen"] = textService_->isKeyboardOpened();

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
	}
	isActivated_ = true;
}

void Client::onDeactivate() {
	json req = createRpcRequest("onDeactivate");
	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
	}
	LangBarButton::clearIconCache();
	isActivated_ = false;
}

bool Client::filterKeyDown(Ime::KeyEvent& keyEvent) {
	json req = createRpcRequest("filterKeyDown");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret, 250);
	if (handleRpcResponse(ret)) {
		return ret.value("return", false);
	}
	return shouldHoldKeyWhenBackendUnavailable(guid_, keyEvent);
}

bool Client::onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	json req = createRpcRequest("onKeyDown");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret, 250);
	if (handleRpcResponse(ret, session)) {
		return ret.value("return", false);
	}
	return shouldHoldKeyWhenBackendUnavailable(guid_, keyEvent);
}

bool Client::filterKeyUp(Ime::KeyEvent& keyEvent) {
	json req = createRpcRequest("filterKeyUp");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret, 250);
	if (handleRpcResponse(ret)) {
		return ret.value("return", false);
	}
	return false;
}

bool Client::onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	json req = createRpcRequest("onKeyUp");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret, 250);
	if (handleRpcResponse(ret, session)) {
		return ret.value("return", false);
	}
	return false;
}

bool Client::onPreservedKey(const GUID& guid) {
	auto guidStr = uuidToString(guid);
	if (!guidStr.empty()) {
		json req = createRpcRequest("onPreservedKey");
		req["guid"] = std::move(guidStr);

		json ret;
		callRpcMethod(req, ret);
		if (handleRpcResponse(ret)) {
			return ret.value("return", false);
		}
	}
	return false;
}

bool Client::onCommand(UINT id, Ime::TextService::CommandType type) {
	json req = createRpcRequest("onCommand");
	req["id"] = id;
	req["type"] = type;

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
		return ret.value("return", false);
	}
	return false;
}

bool Client::sendOnMenu(std::string button_id, json& result) {
	json req = createRpcRequest("onMenu");
	req["id"] = button_id;

	callRpcMethod(req, result);
	if (handleRpcResponse(result)) {
		return true;
	}
	return false;
}

static bool menuFromJson(ITfMenu* pMenu, json& menuInfo) {
	if (pMenu != nullptr && menuInfo.is_array()) {
		for (auto& item : menuInfo) {
			UINT id = item.value("id", 0);
			std::wstring text = utf8ToUtf16(item.value("text", "").c_str());

			DWORD flags = 0;
			json submenuInfo;
			ITfMenu* submenu = nullptr;
			if (id == 0 && text.empty())
				flags = TF_LBMENUF_SEPARATOR;
			else {
				if (item.value("checked", false))
					flags |= TF_LBMENUF_CHECKED;
				if (!item.value("enabled", true))
					flags |= TF_LBMENUF_GRAYED;

				if (item.contains("submenu") && item["submenu"].is_array()) {
					submenuInfo = item["submenu"];
					flags |= TF_LBMENUF_SUBMENU;
				}
			}
			pMenu->AddMenuItem(id, flags, NULL, NULL, text.c_str(), text.length(), flags & TF_LBMENUF_SUBMENU ? &submenu : nullptr);
			if (submenu != nullptr && !submenuInfo.is_null()) {
				menuFromJson(submenu, submenuInfo);
			}
		}
		return true;
	}
	return false;
}

// called when a language bar button needs a menu
// virtual
bool Client::onMenu(LangBarButton* btn, ITfMenu* pMenu) {
	json result;
	if (sendOnMenu(btn->id(), result)) {
		json& menuInfo = result["return"];
		return menuFromJson(pMenu, menuInfo);
	}
	return false;
}

static HMENU menuFromJson(json& menuInfo) {
	if (menuInfo.is_array()) {
		HMENU menu = ::CreatePopupMenu();
		for (auto& item : menuInfo) {
			UINT id = item.value("id", 0);
			std::wstring text = utf8ToUtf16(item.value("text", "").c_str());

			UINT flags = MF_STRING;
			if (id == 0 && text.empty())
				flags = MF_SEPARATOR;
			else {
				if (item.value("checked", false))
					flags |= MF_CHECKED;
				if (!item.value("enabled", true))
					flags |= MF_GRAYED;

				if (item.contains("submenu") && item["submenu"].is_array()) {
					json& subMenuValue = item["submenu"];
					HMENU submenu = menuFromJson(subMenuValue);
					flags |= MF_POPUP;
					id = UINT_PTR(submenu);
				}
			}
			AppendMenu(menu, flags, id, text.c_str());
		}
		return menu;
	}
	return NULL;
}

// called when a language bar button needs a menu
// virtual
HMENU Client::onMenu(LangBarButton* btn) {
	json result;
	if (sendOnMenu(btn->id(), result)) {
		json& menuInfo = result["return"];
		return menuFromJson(menuInfo);
	}
	return NULL;
}

// called when a compartment value is changed
void Client::onCompartmentChanged(const GUID& key) {
	auto guidStr = uuidToString(key);
	if (!guidStr.empty()) {
		json req = createRpcRequest("onCompartmentChanged");
		req["guid"] = std::move(guidStr);

		json ret;
		callRpcMethod(req, ret);
		if (handleRpcResponse(ret)) {
		}
	}
}

// called when the keyboard is opened or closed
void Client::onKeyboardStatusChanged(bool opened) {
	json req = createRpcRequest("onKeyboardStatusChanged");
	req["opened"] = opened;

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
	}
}

// called just before current composition is terminated for doing cleanup.
void Client::onCompositionTerminated(bool forced) {
	json req = createRpcRequest("onCompositionTerminated");
	req["forced"] = forced;

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
	}
}

bool Client::init() {
	json req = createRpcRequest("init");
	req["id"] = guid_.c_str();  // language profile guid
	req["isWindows8Above"] = ::IsWindows8OrGreater();
	req["isMetroApp"] = textService_->isMetroApp();
	req["isUiLess"] = textService_->isUiLess();
	req["isConsole"] = textService_->isConsole();

	json ret;
	return callRpcMethod(req, ret) && handleRpcResponse(ret);
}


json Client::createRpcRequest(const char* methodName) {
	json request;
	request["method"] = methodName;

	// TODO: add other environment info?
	return request;
}

bool Client::callPipeIO(bool isRead, void *buffer, DWORD size, DWORD *rlen, int timeoutMs) {
	if (!ioEvent_ || ioEvent_ == INVALID_HANDLE_VALUE) {
		ioEvent_ = CreateEvent(NULL, TRUE, FALSE, NULL);
	}
	if (!ioEvent_ || ioEvent_ == INVALID_HANDLE_VALUE) {
		return false;
	}

	OVERLAPPED overlapped = { 0 };
	overlapped.hEvent = ioEvent_;
	ResetEvent(ioEvent_);

	BOOL ok;
	if (isRead)
		ok = ReadFile(pipe_, buffer, size, rlen, &overlapped);
	else
		ok = WriteFile(pipe_, buffer, size, rlen, &overlapped);

	if (!ok && GetLastError() != ERROR_IO_PENDING) {
		return false;
	}

	DWORD wait = WaitForSingleObject(ioEvent_, timeoutMs);
	if (wait == WAIT_OBJECT_0) {
		ok = GetOverlappedResult(pipe_, &overlapped, rlen, FALSE);
	}
	else {
		// timeout or error
		CancelIo(pipe_);
		ok = FALSE;
	}

	return ok;
}

bool Client::callRpcPipe(HANDLE pipe, const std::string& serializedRequest, std::string& serializedReply, int timeoutMs) {
	std::string request = serializedRequest;
	if (request.empty() || request.back() != '\n') {
		request += '\n';
	}

	DWORD wlen = 0;
	if (!callPipeIO(false, (void*)request.data(), (DWORD)request.size(), &wlen, timeoutMs)) {
		return false;
	}

	char buf[8192];
	DWORD rlen = 0;
	while (true) {
		// Check if we already have a full line in the buffer
		size_t pos = readBuffer_.find('\n');
		if (pos != std::string::npos) {
			serializedReply = readBuffer_.substr(0, pos); // exclude the newline for easier parsing
			readBuffer_.erase(0, pos + 1);
			return true;
		}

		if (!callPipeIO(true, buf, sizeof(buf), &rlen, timeoutMs) || rlen == 0) {
			return false;
		}
		readBuffer_.append(buf, rlen);
	}
}

// send the request to the server
// a sequence number will be added to the req object automatically.
bool Client::callRpcMethod(json& request, json & response, int timeoutMs) {
	if (shouldWaitConnection_ && !waitForRpcConnection()) {
		return false;
	}

	// Add a sequence number for the request.
	auto seqNum = nextSeqNum_++;
	request["seqNum"] = seqNum;

	std::string serializedRequest = request.dump(); // convert the json object to string

	std::string serializedResponse;
	bool success = false;
	if (callRpcPipe(pipe_, serializedRequest, serializedResponse, timeoutMs)) {
		try {
			response = json::parse(serializedResponse);
			success = true;
			if (response["seqNum"].get<unsigned int>() != seqNum) // sequence number mismatch
				success = false;
		}
		catch (...) {
			success = false;
		}
	}
	else {
		success = false;
	}

	if (!success) { // fail to send the request to the server
		closeRpcConnection(); // close the pipe connection since it's broken
		resetTextServiceState();  // since we lost the connection, the state is unknonw so we reset.
	}
	return success;
}

bool Client::isPipeCreatedByPIMEServer(HANDLE pipe) {
	// security check: make sure that we're connecting to the correct server
	ULONG serverPid;
	if (GetNamedPipeServerProcessId(pipe, &serverPid)) {
		// FIXME: check the command line of the server?
		// See this: http://www.codeproject.com/Articles/19685/Get-Process-Info-with-NtQueryInformationProcess
		// Too bad! Undocumented Windows internal API might be needed here. :-(
	}
	return true;
}

// establish a connection to the specified pipe and returns its handle
// static
HANDLE Client::connectPipe(const wchar_t* pipeName, int timeoutMs) {
	HANDLE pipe = INVALID_HANDLE_VALUE;
	if (WaitNamedPipe(pipeName, timeoutMs)) {
		pipe = CreateFile(pipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, NULL);
	}

	if (pipe != INVALID_HANDLE_VALUE) {
		// The pipe is connected; check if it's created by our server.
		if (!isPipeCreatedByPIMEServer(pipe)) {
			CloseHandle(pipe);
			pipe = INVALID_HANDLE_VALUE;
		}
	}
	return pipe;
}


// Ensure that we're connected to the PIME input method server
// If we are already connected, the method simply returns true;
// otherwise, it tries to establish the connection.
bool Client::waitForRpcConnection() {
	if (pipe_ != INVALID_HANDLE_VALUE) {
		return true;
	}

	wstring serverPipeName = getPipeName(L"Launcher");
	for (int attempt = 0; pipe_ == INVALID_HANDLE_VALUE && attempt < 3; ++attempt) {
		// try to connect to the server
		pipe_ = connectPipe(serverPipeName.c_str(), 3000);
	}

	if (pipe_ != INVALID_HANDLE_VALUE) {
		// send initialization info to the server for hand-shake.
		shouldWaitConnection_ = false;  // prevent recursive call of waitForRpcConnection
		if (!init()) {
			closeRpcConnection();
			shouldWaitConnection_ = true;
			return false;
		}

		if (isActivated_) {
			// we lost connection while being activated previously
			// re-initialize the whole text service.
			// activate the text service again.
			onActivate();
		}
		shouldWaitConnection_ = true;
	}
	// if init() or onActivate() RPC fails, the pipe_ might have been closed.
	return pipe_ != INVALID_HANDLE_VALUE;
}

void Client::resetTextServiceState() {
	// we lost connection while being activated previously
	// re-initialize the whole text service.

	// cleanup for the previous instance.
	// remove all buttons

	// some language bar buttons are not unregistered properly
	if (!buttons_.empty()) {
		for (auto& item : buttons_) {
			textService_->removeButton(item.second);
		}
		buttons_.clear();
	}
}

void Client::closeRpcConnection() {
	if (pipe_ != INVALID_HANDLE_VALUE) {
		CloseHandle(pipe_);
		pipe_ = INVALID_HANDLE_VALUE;
	}
	if (ioEvent_ && ioEvent_ != INVALID_HANDLE_VALUE) {
		CloseHandle(ioEvent_);
		ioEvent_ = NULL;
	}
	readBuffer_.clear();
}

wstring Client::getPipeName(const wchar_t* base_name) {
	wstring pipeName = L"\\\\.\\pipe\\";
	DWORD len = 0;
	::GetUserNameW(NULL, &len); // get the required size of the buffer
	if (len <= 0)
		return false;
	// add username to the pipe path so it won't clash with the other users' pipes
	unique_ptr<wchar_t[]> username(new wchar_t[len]);
	if (!::GetUserNameW(username.get(), &len))
		return false;
	pipeName += username.get();
	pipeName += L"\\PIME\\";
	pipeName += base_name;
	return pipeName;
}


} // namespace PIME
