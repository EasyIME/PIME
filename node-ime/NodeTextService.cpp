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

#include "NodeTextService.h"
#include <assert.h>
#include <string>
#include <libIME/Utils.h>
#include <libIME/LangBarButton.h>
#include "NodeImeModule.h"
#include "resource.h"
#include <Shellapi.h>
#include <sys/stat.h>

using namespace std;

namespace Node {

// {B59D51B9-B832-40D2-9A8D-56959372DDC7}
static const GUID g_modeButtonGuid = // English/Chinses mode switch
{ 0xb59d51b9, 0xb832, 0x40d2, { 0x9a, 0x8d, 0x56, 0x95, 0x93, 0x72, 0xdd, 0xc7 } };

// {5325DBF5-5FBE-467B-ADF0-2395BE9DD2BB}
static const GUID g_shapeTypeButtonGuid = // half shape/full shape switch
{ 0x5325dbf5, 0x5fbe, 0x467b, { 0xad, 0xf0, 0x23, 0x95, 0xbe, 0x9d, 0xd2, 0xbb } };

// {4FAFA520-2104-407E-A532-9F1AAB7751CD}
static const GUID g_settingsButtonGuid = // settings button/menu
{ 0x4fafa520, 0x2104, 0x407e, { 0xa5, 0x32, 0x9f, 0x1a, 0xab, 0x77, 0x51, 0xcd } };

// {C77A44F5-DB21-474E-A2A2-A17242217AB3}
static const GUID g_shiftSpaceGuid = // shift + space
{ 0xc77a44f5, 0xdb21, 0x474e, { 0xa2, 0xa2, 0xa1, 0x72, 0x42, 0x21, 0x7a, 0xb3 } };

// {F4D1E543-FB2C-48D7-B78D-20394F355381} // global compartment GUID for config change notification
static const GUID g_configChangedGuid = 
{ 0xf4d1e543, 0xfb2c, 0x48d7, { 0xb7, 0x8d, 0x20, 0x39, 0x4f, 0x35, 0x53, 0x81 } };

// this is the GUID of the IME mode icon in Windows 8
// the value is not available in older SDK versions, so let's define it ourselves.
static const GUID _GUID_LBI_INPUTMODE =
{ 0x2C77A81E, 0x41CC, 0x4178, { 0xA3, 0xA7, 0x5F, 0x8A, 0x98, 0x75, 0x68, 0xE6 } };

TextService::TextService(ImeModule* module):
	Ime::TextService(module),
	client_(nullptr),
	messageWindow_(nullptr),
	messageTimerId_(0),
	candidateWindow_(nullptr),
	imeModeIcon_(nullptr) {

	// add preserved keys
	addPreservedKey(VK_SPACE, TF_MOD_SHIFT, g_shiftSpaceGuid); // shift + space

	// add language bar buttons
	// siwtch Chinese/English modes
#if 0
	switchLangButton_ = new Ime::LangBarButton(this, g_modeButtonGuid, ID_SWITCH_LANG);
	switchLangButton_->setTooltip(IDS_SWITCH_LANG);
	addButton(switchLangButton_);

	// toggle full shape/half shape
	switchShapeButton_ = new Ime::LangBarButton(this, g_shapeTypeButtonGuid, ID_SWITCH_SHAPE);
	switchShapeButton_->setTooltip(IDS_SWITCH_SHAPE);
	addButton(switchShapeButton_);

	// settings and others, may open a popup menu
	Ime::LangBarButton* button = new Ime::LangBarButton(this, g_settingsButtonGuid);
	button->setTooltip(IDS_SETTINGS);
	button->setIcon(IDI_CONFIG);
	HMENU menu = ::LoadMenuW(this->imeModule()->hInstance(), LPCTSTR(IDR_MENU));
	popupMenu_ = ::GetSubMenu(menu, 0);
	button->setMenu(popupMenu_);
	addButton(button);
	button->Release();

	// Windows 8 systray IME mode icon
	if(imeModule()->isWindows8Above()) {
		imeModeIcon_ = new Ime::LangBarButton(this, _GUID_LBI_INPUTMODE, ID_MODE_ICON);
		imeModeIcon_->setIcon(IDI_ENG);
		addButton(imeModeIcon_);
	}
#endif

	// global compartment stuff
	addCompartmentMonitor(g_configChangedGuid, true);

	// font for candidate and mesasge windows
#if 0
	font_ = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
	LOGFONT lf;
	GetObject(font_, sizeof(lf), &lf);
	lf.lfHeight = config().fontSize;
	lf.lfWeight = FW_NORMAL;
	font_ = CreateFontIndirect(&lf);
#endif
}

TextService::~TextService(void) {
	if(client_)
		delete client_;

	if(popupMenu_)
		::DestroyMenu(popupMenu_);

	if(candidateWindow_)
		delete candidateWindow_;

	if(messageWindow_)
		hideMessage();

	if(font_)
		::DeleteObject(font_);

	if(switchLangButton_)
		switchLangButton_->Release();
	if(switchShapeButton_)
		switchShapeButton_->Release();
	if(imeModeIcon_)
		imeModeIcon_->Release();
}

// virtual
void TextService::onActivate() {
	if(!client_)
		client_ = new Client(this);
	client_->onActivate();

	DWORD configStamp = globalCompartmentValue(g_configChangedGuid);
	updateLangButtons();
	if(imeModeIcon_) // windows 8 IME mode icon
		imeModeIcon_->setEnabled(isKeyboardOpened());
}

// virtual
void TextService::onDeactivate() {
	if(client_) {
		client_->onDeactivate();
		delete client_;
		client_ = NULL;
	}

	hideMessage();

	if(candidateWindow_) {
		showingCandidates_ = false;
		delete candidateWindow_;
		candidateWindow_ = NULL;
	}
}

// virtual
void TextService::onFocus() {
}

// virtual
bool TextService::filterKeyDown(Ime::KeyEvent& keyEvent) {
	if(!client_)
		return false;
	return client_->filterKeyDown(keyEvent);
}

// virtual
bool TextService::onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	if(!client_)
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
#if 0
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

	if(imeModeIcon_)
		imeModeIcon_->setEnabled(opened);
	// FIXME: should we also disable other language bar buttons as well?
#endif
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
	}
	if(client_)
		client_->onCompositionTerminated(forced);
}

void TextService::onLangProfileActivated(REFIID lang) {
	if(client_)
		client_->onLangProfileActivated(lang);
}

void TextService::onLangProfileDeactivated(REFIID lang) {
	if(client_)
		client_->onLangProfileDeactivated(lang);
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
	if(!candidateWindow_) {
		candidateWindow_ = new Ime::CandidateWindow(this, session);
		candidateWindow_->setFont(font_);
	}
	// updateCandidates(session);
	candidateWindow_->show();
	showingCandidates_ = true;
}

// hide candidate list window
void TextService::hideCandidates() {
	assert(candidateWindow_);
	if(candidateWindow_) {
		delete candidateWindow_;
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
		TextService* pThis = (Node::TextService*)messageWindow->textService();
		pThis->onMessageTimeout();
	}
}


void TextService::updateLangButtons() {
}


} // namespace Node
