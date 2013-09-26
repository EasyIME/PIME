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

#ifndef CHEWING_TEXT_SERVICE_H
#define CHEWING_TEXT_SERVICE_H

#include <LibIME/TextService.h>
#include <LibIME/CandidateWindow.h>
#include <LibIME/MessageWindow.h>
#include <LibIME/EditSession.h>
#include <LibIME/LangBarButton.h>
#include <chewing.h>
#include "ChewingImeModule.h"
#include <sys/types.h>

namespace Chewing {

class TextService: public Ime::TextService {
public:
	TextService(ImeModule* module);
	virtual ~TextService(void);

	virtual void onActivate();
	virtual void onDeactivate();

	virtual void onFocus();

	virtual bool filterKeyDown(Ime::KeyEvent& keyEvent);
	virtual bool onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session);

	virtual bool filterKeyUp(Ime::KeyEvent& keyEvent);
	virtual bool onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session);

	virtual bool onPreservedKey(const GUID& guid);

	virtual bool onCommand(UINT id, CommandType type);

	// called when a compartment value is changed
	virtual void onCompartmentChanged(const GUID& key);

	// called when the keyboard is opened or closed
	virtual void onKeyboardStatusChanged(bool opened);

	// called just before current composition is terminated for doing cleanup.
	// if forced is true, the composition is terminated by others, such as
	// the input focus is grabbed by another application.
	// if forced is false, the composition is terminated gracefully by endComposition().
	virtual void onCompositionTerminated(bool forced);

	ChewingContext* chewingContext() {
		return chewingContext_;
	}

	Config& config() {
		return static_cast<ImeModule*>(imeModule())->config();
	}

private:
	void initChewingContext(); // initialize chewing context
	void freeChewingContext(); // free chewing context

	bool hasCandidates() {
		return ::chewing_cand_TotalChoice(chewingContext_) > 0;
	}

	bool showingCandidates() {
		return showingCandidates_;
	}

	// candidate window
	void showCandidates(Ime::EditSession* session);
	void updateCandidates(Ime::EditSession* session);
	void hideCandidates();

	// message window
	void showMessage(Ime::EditSession* session, std::wstring message, int duration = 3);
	void hideMessage();
	void onMessageTimeout();
	static void CALLBACK onMessageTimeout(HWND hwnd, UINT msg, UINT_PTR id, DWORD time);

	void updateLangButtons(); // update status of language bar buttons

	// reload configurations if changes are detected
	void reloadConfigIfNeeded();

	// apply current configurations to chewing context
	void applyConfig();

	void toggleLanguageMode(); // toggle between English and Chinese
	void toggleShapeMode(); // toggle between full shape and half shape
	void toggleSimplifiedChinese(); // toggle output traditional or simplified Chinese

private:
	ChewingContext* chewingContext_;
	Ime::CandidateWindow* candidateWindow_;
	bool showingCandidates_;
	Ime::MessageWindow* messageWindow_;
	UINT messageTimerId_;
	HFONT font_;

	Ime::LangBarButton* switchLangButton_;
	Ime::LangBarButton* switchShapeButton_;
	Ime::LangBarButton* imeModeIcon_; // IME mode icon, a special language button (Windows 8 only)
	HMENU popupMenu_;

	bool outputSimpChinese_; // output simplified Chinese
	int langMode_;
	int shapeMode_;
	time_t symbolsFileTime_; // mtime of symbols.dat file

	UINT lastKeyDownCode_;
};

}

#endif
