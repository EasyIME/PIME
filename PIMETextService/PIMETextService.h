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

#ifndef NODE_TEXT_SERVICE_H
#define NODE_TEXT_SERVICE_H

#include <LibIME2/src/TextService.h>
#include <LibIME2/src/CandidateWindow.h>
#include <LibIME2/src/MessageWindow.h>
#include <LibIME2/src/EditSession.h>
#include <LibIME2/src/LangBarButton.h>
#include "PIMEImeModule.h"
#include <sys/types.h>
#include "PIMEClient.h"
#include <memory>


namespace PIME {

class TextService: public Ime::TextService {
	friend class Client;
public:
	TextService(ImeModule* module);

	virtual void onActivate();
	virtual void onDeactivate();

	virtual void onFocus();

	virtual bool filterKeyDown(Ime::KeyEvent& keyEvent);
	virtual bool onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session);

	virtual bool filterKeyUp(Ime::KeyEvent& keyEvent);
	virtual bool onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session);

	virtual bool onPreservedKey(const GUID& guid);

	virtual bool onCommand(UINT id, CommandType type);

	// called when a language bar button needs a menu
	virtual bool onMenu(LangBarButton* btn, ITfMenu* pMenu);

	// called when a language bar button needs a menu
	virtual HMENU onMenu(LangBarButton* btn);

	// called when a compartment value is changed
	virtual void onCompartmentChanged(const GUID& key);

	// called when the keyboard is opened or closed
	virtual void onKeyboardStatusChanged(bool opened);

	// called just before current composition is terminated for doing cleanup.
	// if forced is true, the composition is terminated by others, such as
	// the input focus is grabbed by another application.
	// if forced is false, the composition is terminated gracefully by endComposition().
	virtual void onCompositionTerminated(bool forced);

	virtual void onLangProfileActivated(REFIID lang);

	virtual void onLangProfileDeactivated(REFIID lang);

	// methods called by PIME::Client
	int candPerRow() const {
		return candPerRow_;
	}

	void setCandPerRow(int candPerRow) {
		candPerRow_ = candPerRow;
	}

	std::wstring selKeys() const {
		return selKeys_;
	}

	void setSelKeys(std::wstring selKeys) {
		selKeys_ = selKeys;
	}

	bool candUseCursor() const {
		return candUseCursor_;
	}

	void setCandUseCursor(bool candUseCursor) {
		candUseCursor_ = candUseCursor;
	}

	std::wstring candFontName() const {
		return candFontName_;
	}

	void setCandFontName(std::wstring candFontName) {
		candFontName_ = candFontName;
		updateFont_ = true;
	}

	int candFontSize() {
		return candFontSize_;
	}

	void setCandFontSize(int candFontSize) {
		candFontSize_ = candFontSize;
		updateFont_ = true;
	}

	bool showingCandidates() {
		return showingCandidates_;
	}

	const std::wstring& candidateHeader() const {
		return candidateHeader_;
	}

	void setCandidateHeader(const std::wstring& header) {
		candidateHeader_ = header;
	}

	void setCandidatePageInfo(const std::wstring& info) {
		candidatePageInfo_ = info;
	}

	void setCandidateMessage(const std::wstring& message) {
		candidateMessage_ = message;
	}

	void setCandidateTheme(COLORREF panelBackground,
		COLORREF panelBorder,
		COLORREF textPrimary,
		COLORREF textSecondary,
		COLORREF highlightBackground,
		COLORREF highlightBorder,
		COLORREF highlightText);

	void setCandidateSpacing(int contentMargin, int textMargin, int borderRadius);

	void setCandidateKeyStyle(int keyStyle) {
		if (candidateKeyStyle_ == keyStyle)
			return;
		candidateKeyStyle_ = keyStyle;
		applyCandidateWindowStyle();
	}

	void setCandidateMessageStyle(int messageStyle) {
		if (candidateMessageStyle_ == messageStyle && candidateMessageDisplayStyle_ == messageStyle)
			return;
		candidateMessageStyle_ = messageStyle;
		candidateMessageDisplayStyle_ = messageStyle;
		applyCandidateWindowStyle();
	}

	void setCandidateMessageDisplayStyle(int messageStyle) {
		if (candidateMessageDisplayStyle_ == messageStyle)
			return;
		candidateMessageDisplayStyle_ = messageStyle;
		if (candidateWindow_)
			candidateWindow_->setMessageStyle(candidateMessageDisplayStyle_);
	}

	void resetCandidateMessageDisplayStyle() {
		setCandidateMessageDisplayStyle(candidateMessageStyle_);
	}

	void setCandidateStableWidth(bool enabled, int minWidth) {
		if (candidateStableWidth_ == enabled && candidateMinWidth_ == minWidth)
			return;
		candidateStableWidth_ = enabled;
		candidateMinWidth_ = minWidth;
		applyCandidateWindowStyle();
	}

	void setCandidateMaxWidth(bool wrapToMaxWidth, int maxWidth) {
		if (candidateWrapToMaxWidth_ == wrapToMaxWidth && candidateMaxWidth_ == maxWidth)
			return;
		candidateWrapToMaxWidth_ = wrapToMaxWidth;
		candidateMaxWidth_ = maxWidth;
		applyCandidateWindowStyle();
	}

	void setCandidateEdgeAvoidance(bool enabled) {
		candidateEdgeAvoidance_ = enabled;
	}

	void setCandidateModernStyle(bool enabled) {
		candidateModernStyle_ = enabled;
		applyCandidateWindowStyle();
	}

	bool candidateModernStyle() const {
		return candidateModernStyle_;
	}

	// candidate window
	void showCandidates(Ime::EditSession* session);
	void updateCandidates(Ime::EditSession* session);
    void updateCandidatesWindow(Ime::EditSession* session);
	void hideCandidates();

	void refreshCandidates();

	// message window
	void showMessage(Ime::EditSession* session, std::wstring message, int duration = 3);
    void updateMessageWindow(Ime::EditSession* session);
	void hideMessage();

private:
	virtual ~TextService(void);  // COM object should only be deleted using Release()

	void onMessageTimeout();
	static void CALLBACK onMessageTimeout(HWND hwnd, UINT msg, UINT_PTR id, DWORD time);

	void updateLangButtons(); // update status of language bar buttons

	void createCandidateWindow(Ime::EditSession* session);
	void applyCandidateWindowStyle();
	void moveCandidateWindow(Ime::EditSession* session);
	int candFontHeight();

	void closeClient();

private:
	bool validCandidateListElementId_;
	DWORD candidateListElementId_;
	Ime::ComPtr<Ime::CandidateWindow> candidateWindow_; // this is a ref-counted COM object and should not be managed with std::unique_ptr
	bool showingCandidates_;
	std::vector<std::wstring> candidates_; // current candidate list
	std::unique_ptr<Ime::MessageWindow> messageWindow_;
	UINT messageTimerId_;
	HFONT font_;
	bool updateFont_;
	int candPerRow_;
	std::wstring selKeys_;
	bool candUseCursor_;
	std::wstring candFontName_;
	std::wstring candidateHeader_;
	std::wstring candidatePageInfo_;
	std::wstring candidateMessage_;
	int candFontSize_;
	bool candidateModernStyle_;
	bool candidateEdgeAvoidance_;
	COLORREF candidatePanelBackground_;
	COLORREF candidatePanelBorder_;
	COLORREF candidateTextPrimary_;
	COLORREF candidateTextSecondary_;
	COLORREF candidateHighlightBackground_;
	COLORREF candidateHighlightBorder_;
	COLORREF candidateHighlightText_;
	int candidateContentMargin_;
	int candidateTextMargin_;
	int candidateBorderRadius_;
	int candidateKeyStyle_;
	int candidateMessageStyle_;
	int candidateMessageDisplayStyle_;
	bool candidateStableWidth_;
	int candidateMinWidth_;
	bool candidateWrapToMaxWidth_;
	int candidateMaxWidth_;

	HMENU popupMenu_;

	std::unique_ptr<Client> client_; // connection client
	GUID currentLangProfile_;
};

}

#endif
