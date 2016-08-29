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

#include "PIMETextService.h"
#include <assert.h>
#include <string>
#include <libIME/ComPtr.h>
#include <libIME/Utils.h>
#include <libIME/LangBarButton.h>
#include "PIMEImeModule.h"
#include "resource.h"
#include <Shellapi.h>
#include <sys/stat.h>

using namespace std;

namespace PIME {

TextService::TextService(ImeModule* module):
	Ime::TextService(module),
	client_(nullptr),
	messageWindow_(nullptr),
	messageTimerId_(0),
	validCandidateListElementId_(false),
	candidateListElementId_(0),
	candidateWindow_(nullptr),
	showingCandidates_(false),
	updateFont_(false),
	candPerRow_(10),
	selKeys_(L"1234567890"),
	candUseCursor_(false),
	candFontSize_(12),
	imeModeIcon_(nullptr),
	currentLangProfile_(IID_NULL) {

	// font for candidate and mesasge windows
	font_ = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
	LOGFONT lf;
	GetObject(font_, sizeof(lf), &lf);
	lf.lfHeight = candFontHeight(); // FIXME: make this configurable
	lf.lfWeight = FW_NORMAL;
	font_ = CreateFontIndirect(&lf);
}

TextService::~TextService(void) {
	if(client_)
		delete client_;

	if(popupMenu_)
		::DestroyMenu(popupMenu_);

	if (candidateWindow_) {
		hideCandidates();
		candidateWindow_->Release();
	}

	if(messageWindow_)
		hideMessage();

	if(font_)
		::DeleteObject(font_);

	if(imeModeIcon_)
		imeModeIcon_->Release();
}

// virtual
void TextService::onActivate() {
	// Since we support multiple language profiles in this text service,
	// we do nothing when the whole text service is activated.
	// Instead, we do the actual initilization for each language profile when it is activated.
	// In PIME, we create different client connections for different language profiles.
}

// virtual
void TextService::onDeactivate() {
	if(client_) {
		// Windows does not deactivate current language profile before
		// deactivating the whole text service. Let's do it ourselves.
		if (!::IsEqualIID(currentLangProfile_, IID_NULL)) {
			onLangProfileDeactivated(currentLangProfile_);
		}
	}
}

// virtual
void TextService::onFocus() {
}

// virtual
bool TextService::filterKeyDown(Ime::KeyEvent& keyEvent) {
	// if (keyEvent.isKeyToggled(VK_CAPITAL))
	//	return true;
	if(!client_)
		return false;
	return client_->filterKeyDown(keyEvent);
}

// virtual
bool TextService::onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	//if (keyEvent.isKeyToggled(VK_CAPITAL))
	//	return true;
	if (!client_)
		return false;
	return client_->onKeyDown(keyEvent, session);
}

// virtual
bool TextService::filterKeyUp(Ime::KeyEvent& keyEvent) {
	if(!client_)
		return false;
	return client_->filterKeyUp(keyEvent);
}

// virtual
bool TextService::onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	if(!client_)
		return false;
	return client_->onKeyUp(keyEvent, session);
}

// virtual
bool TextService::onPreservedKey(const GUID& guid) {
	if(!client_)
		return false;
	// some preserved keys registered in ctor are pressed
	return client_->onPreservedKey(guid);
}


// virtual
bool TextService::onCommand(UINT id, CommandType type) {
	if(!client_)
		return false;
	return client_->onCommand(id, type);
}


// called when a language bar button needs a menu
// virtual
bool TextService::onMenu(LangBarButton* btn, ITfMenu* pMenu) {
	if (client_ != nullptr) {
		return client_->onMenu(btn, pMenu);
	}
	return false;
}

// called when a language bar button needs a menu
// virtual
HMENU TextService::onMenu(LangBarButton* btn) {
	if (client_ != nullptr) {
		return client_->onMenu(btn);
	}
	return NULL;
}


// virtual
void TextService::onCompartmentChanged(const GUID& key) {
	Ime::TextService::onCompartmentChanged(key);
	if(client_)
		client_->onCompartmentChanged(key);
}

// called when the keyboard is opened or closed
// virtual
void TextService::onKeyboardStatusChanged(bool opened) {
	Ime::TextService::onKeyboardStatusChanged(opened);
	if(client_)
		client_->onKeyboardStatusChanged(opened);
	if(opened) { // keyboard is opened
	}
	else { // keyboard is closed
		if(isComposing()) {
			// end current composition if needed
			ITfContext* context = currentContext();
			if(context) {
				endComposition(context);
				context->Release();
			}
		}
		if(showingCandidates()) // disable candidate window if it's opened
			hideCandidates();
		hideMessage(); // hide message window, if there's any
	}
}

// called just before current composition is terminated for doing cleanup.
// if forced is true, the composition is terminated by others, such as
// the input focus is grabbed by another application.
// if forced is false, the composition is terminated gracefully by endComposition().
// virtual
void TextService::onCompositionTerminated(bool forced) {
	// we do special handling here for forced composition termination.
	if(forced) {
		// we're still editing our composition and have something in the preedit buffer.
		// however, some other applications grabs the focus and force us to terminate
		// our composition.
		if (showingCandidates()) // disable candidate window if it's opened
			hideCandidates();
		hideMessage(); // hide message window, if there's any
	}
	if(client_)
		client_->onCompositionTerminated(forced);
}

void TextService::onLangProfileActivated(REFIID lang) {
	// Sometimes, Windows does not deactivate the old language profile before
	// activating the new one. So here we do it by ourselves.
	// If a new profile is activated, but there is an old one remaining active,
	// deactive it first.
	if (!::IsEqualIID(currentLangProfile_, IID_NULL)) {
		// deactivate the current profile
		onLangProfileDeactivated(currentLangProfile_);
	}

	if (client_ != nullptr) {
		return;
	}

	// create a new client connection to the input method server for the language profile
	if (!client_) {
		client_ = new Client(this, lang);
	}
	client_->onActivate();

	if (imeModeIcon_) // windows 8 IME mode icon
		imeModeIcon_->setEnabled(isKeyboardOpened());
	currentLangProfile_ = lang;
}

void TextService::onLangProfileDeactivated(REFIID lang) {
	if (::IsEqualIID(lang, currentLangProfile_)) {
		// deactive currently active language profile
		if (client_) {
			// disconnect from the server
			client_->onDeactivate();
			currentLangProfile_ = IID_NULL;
			delete client_;
			client_ = NULL;
			// detroy UI resources
			hideMessage();
			hideCandidates();
		}
		currentLangProfile_ = IID_NULL;
	}
}

void TextService::createCandidateWindow(Ime::EditSession* session) {
	if (!candidateWindow_) {
		candidateWindow_ = new Ime::CandidateWindow(this, session);
		candidateWindow_->setFont(font_);
		Ime::ComQIPtr<ITfUIElementMgr> elementMgr = threadMgr();
		if (elementMgr) {
			BOOL pbShow = false;
			if (validCandidateListElementId_ =
				(elementMgr->BeginUIElement(candidateWindow_, &pbShow, &candidateListElementId_) == S_OK)) {
				candidateWindow_->Show(pbShow);
			}
		}
	}
}

void TextService::updateCandidates(Ime::EditSession* session) {
	createCandidateWindow(session);
	candidateWindow_->clear();

	// FIXME: is this the right place to do it?
	if (updateFont_) {
		// font for candidate and mesasge windows
		LOGFONT lf;
		GetObject(font_, sizeof(lf), &lf);
		::DeleteObject(font_); // delete old font
		lf.lfHeight = candFontHeight(); // apply the new size
		if (!candFontName_.empty()) { // apply new font name
			wcsncpy(lf.lfFaceName, candFontName_.c_str(), 31);
		}
		font_ = CreateFontIndirect(&lf); // create new font
		// if (messageWindow_)
		//	messageWindow_->setFont(font_);
		if (candidateWindow_)
			candidateWindow_->setFont(font_);
		updateFont_ = false;
	}

	candidateWindow_->setUseCursor(candUseCursor_);
	candidateWindow_->setCandPerRow(candPerRow_);

	// the items in the candidate list should not exist the
	// number of available keys used to select them.
	assert(candidates_.size() <= selKeys_.size());
	for (int i = 0; i < candidates_.size(); ++i) {
		candidateWindow_->add(candidates_[i], selKeys_[i]);
	}
	candidateWindow_->recalculateSize();
	candidateWindow_->refresh();

	RECT textRect;
	// get the position of composition area from TSF
	if (selectionRect(session, &textRect)) {
		// FIXME: where should we put the candidate window?
		candidateWindow_->move(textRect.left, textRect.bottom);
	}

	if (validCandidateListElementId_) {
		Ime::ComQIPtr<ITfUIElementMgr> elementMgr = threadMgr();
		if (elementMgr) {
			elementMgr->UpdateUIElement(candidateListElementId_);
		}
	}
}

void TextService::refreshCandidates() {
	if (validCandidateListElementId_) {
		Ime::ComQIPtr<ITfUIElementMgr> elementMgr = threadMgr();
		if (elementMgr) {
			elementMgr->UpdateUIElement(candidateListElementId_);
		}
	}
}

// show candidate list window
void TextService::showCandidates(Ime::EditSession* session) {
	// TODO: implement ITfCandidateListUIElement interface to support UI less mode
	// Great reference: http://msdn.microsoft.com/en-us/library/windows/desktop/aa966970(v=vs.85).aspx

	// NOTE: in Windows 8 store apps, candidate window should be owned by
	// composition window, which can be returned by TextService::compositionWindow().
	// Otherwise, the candidate window cannot be shown.
	// Ime::CandidateWindow handles this internally. If you create your own
	// candidate window, you need to call TextService::isImmersive() to check
	// if we're in a Windows store app. If isImmersive() returns true,
	// The candidate window created should be a child window of the composition window.
	// Please see Ime::CandidateWindow::CandidateWindow() for an example.
	createCandidateWindow(session);
	showingCandidates_ = true;
}

// hide candidate list window
void TextService::hideCandidates() {
	assert(candidateWindow_);
	if (validCandidateListElementId_) {
		Ime::ComQIPtr<ITfUIElementMgr> elementMgr = threadMgr();
		if (elementMgr) {
			elementMgr->EndUIElement(candidateListElementId_);
			candidateListElementId_ = 0;
			validCandidateListElementId_ = false;
		}
	}
	if(candidateWindow_) {
		candidateWindow_->Release();
		candidateWindow_ = NULL;
	}
	showingCandidates_ = false;
}

// message window
void TextService::showMessage(Ime::EditSession* session, std::wstring message, int duration) {
	// remove previous message if there's any
	hideMessage();
	// FIXME: reuse the window whenever possible
	messageWindow_ = new Ime::MessageWindow(this, session);
	messageWindow_->setFont(font_);
	messageWindow_->setText(message);
	
	int x = 0, y = 0;
	if(isComposing()) {
		RECT rc;
		if(selectionRect(session, &rc)) {
			x = rc.left;
			y = rc.bottom;
		}
	}
	messageWindow_->move(x, y);
	messageWindow_->show();

	messageTimerId_ = ::SetTimer(messageWindow_->hwnd(), 1, duration * 1000, (TIMERPROC)TextService::onMessageTimeout);
}

void TextService::hideMessage() {
	if(messageTimerId_) {
		::KillTimer(messageWindow_->hwnd(), messageTimerId_);
		messageTimerId_ = 0;
	}
	if(messageWindow_) {
		delete messageWindow_;
		messageWindow_ = NULL;
	}
}

// called when the message window timeout
void TextService::onMessageTimeout() {
	hideMessage();
}

// static
void CALLBACK TextService::onMessageTimeout(HWND hwnd, UINT msg, UINT_PTR id, DWORD time) {
	Ime::MessageWindow* messageWindow = (Ime::MessageWindow*)Ime::Window::fromHwnd(hwnd);
	assert(messageWindow);
	if(messageWindow) {
		TextService* pThis = (PIME::TextService*)messageWindow->textService();
		pThis->onMessageTimeout();
	}
}


void TextService::updateLangButtons() {
}

int TextService::candFontHeight() {
	int candFontHeight_ = candFontSize_;
	HDC hdc = GetDC(NULL);
	if (hdc)
	{
		candFontHeight_ = -MulDiv(candFontSize_, GetDeviceCaps(hdc, LOGPIXELSY), 72);
		ReleaseDC(NULL, hdc);
	}
	return candFontHeight_;
}
} // namespace PIME
