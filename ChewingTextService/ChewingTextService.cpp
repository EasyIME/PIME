#include "ChewingTextService.h"
#include <assert.h>
#include <string>
#include <libIME/Utils.h>
#include <libIME/LangBarButton.h>
#include <libIME/Dialog.h>
#include <libIME/PropertyDialog.h>
#include "ChewingImeModule.h"
#include "resource.h"
#include <Shellapi.h>
#include "TypingPage.h"

using namespace Chewing;
using namespace std;

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

// {A39B40FD-479C-4DBE-B865-EFC8969A518D}
static const GUID g_shiftUpGuid = // shift alone, key up
{ 0xa39b40fd, 0x479c, 0x4dbe, { 0xb8, 0x65, 0xef, 0xc8, 0x96, 0x9a, 0x51, 0x8d } };

TextService::TextService(ImeModule* module):
	Ime::TextService(module),
	showingCandidates_(false),
	langMode_(-1),
	shapeMode_(-1),
	candidateWindow_(NULL),
	chewingContext_(NULL) {

	// add preserved keys
	addPreservedKey(VK_SPACE, TF_MOD_SHIFT, g_shiftSpaceGuid); // shift + space
	addPreservedKey(VK_SHIFT, TF_MOD_ON_KEYUP, g_shiftUpGuid); // shift alone, key up

	// add language bar buttons
	// siwtch Chinese/English modes
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
	HMENU popup = ::GetSubMenu(menu, 0);
	button->setMenu(popup);
	addButton(button);
	button->Release();
}

TextService::~TextService(void) {
	if(candidateWindow_)
		delete candidateWindow_;

	if(switchLangButton_)
		switchLangButton_->Release();
	if(switchShapeButton_)
		switchShapeButton_->Release();

	if(chewingContext_)
		::chewing_delete(chewingContext_);
}

// virtual
void TextService::onActivate() {
	if(!chewingContext_) {
		chewingContext_ = ::chewing_new();
		::chewing_set_maxChiSymbolLen(chewingContext_, 50);
	}

	updateLangButtons();
}

// virtual
void TextService::onDeactivate() {
	if(chewingContext_) {
		::chewing_delete(chewingContext_);
		chewingContext_ = NULL;
	}

	if(candidateWindow_) {
		delete candidateWindow_;
		candidateWindow_ = NULL;
	}
}

// virtual
void TextService::onFocus() {
}

// virtual
bool TextService::filterKeyDown(Ime::KeyEvent& keyEvent) {
	// return false if we don't need this key
	assert(chewingContext_);

	// check if we're in Chinses or English mode
	if(langMode_ != CHINESE_MODE) // don't do anything in English mode
		return false;

	if(!isComposing()) {
		if(keyEvent.isKeyToggled(VK_CAPITAL)) { // Caps lock is on => English mode
			// FIXME: should we change chewing mode to ENGLISH_MODE?
			return false; // bypass IME
		}

		if(keyEvent.isKeyToggled(VK_NUMLOCK)) { // NumLock is on
			// if this key is Num pad 0-9, +, -, *, /, pass it back to the system
			if(keyEvent.keyCode() >= VK_NUMPAD0 && keyEvent.keyCode() <= VK_DIVIDE)
				return false; // bypass IME
		}

		if(keyEvent.isKeyDown(VK_CONTROL) || keyEvent.isKeyDown(VK_MENU)) { // if Ctrl or Alt key is down
			if(isComposing()) {
				// FIXME: we need Ctrl + num in libchewing?
			}
			return false; // bypass IME. This might be a shortcut key used in the application
		}

		// when not composing, we only cares about Bopomopho
		// FIXME: we should check if the key is mapped to a phonetic symbol instead
		if(keyEvent.isChar() && isgraph(keyEvent.charCode())) {
			// this is a key mapped to a printable char. we want it!
			return true;
		}
		return false;
	}
	return true;
}

// virtual
bool TextService::onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	assert(chewingContext_);
	// FIXME: the following keys are not handled:
	// shift + left		VK_LSHIFT
	// shift + right		VK_RSHIFT
	// do we really need to support this feature?

	// set this to true or false according to the status of Shift key
	::chewing_set_easySymbolInput(chewingContext_, keyEvent.isKeyDown(VK_SHIFT));

	UINT charCode = keyEvent.charCode();
	if(charCode && isprint(charCode)) { // printable characters (exclude extended keys?)

		// If Caps lock is on, temporarily change to English mode
		if(keyEvent.isKeyToggled(VK_CAPITAL) || langMode_ == SYMBOL_MODE) {
			int oldLangMode = ::chewing_get_ChiEngMode(chewingContext_);
			::chewing_set_ChiEngMode(chewingContext_, SYMBOL_MODE); // change to English mode temporarily
			if(isalpha(charCode)) { // a-z
				// reverse upper and lower case
				if(isupper(charCode))
					::chewing_handle_Default(chewingContext_, tolower(charCode));
				else
					::chewing_handle_Default(chewingContext_, toupper(charCode));
			}
			else
				::chewing_handle_Default(chewingContext_, charCode);
			::chewing_set_ChiEngMode(chewingContext_, oldLangMode); // restore previous mode
		}
		else { // Chinese mode
			if(isalpha(charCode)) // alphabets: A-Z
				::chewing_handle_Default(chewingContext_, tolower(charCode));
			else if(keyEvent.keyCode() == VK_SPACE) // space key
				::chewing_handle_Space(chewingContext_);
			else if(keyEvent.isKeyDown(VK_CONTROL) && isdigit(charCode)) // Ctrl + number (0~9)
				::chewing_handle_CtrlNum(chewingContext_, charCode);
			else if(keyEvent.isKeyToggled(VK_NUMLOCK) && keyEvent.keyCode() >= VK_NUMPAD0 && keyEvent.keyCode() <= VK_DIVIDE)
				// numlock is on, handle numpad keys
				::chewing_handle_Numlock(chewingContext_, charCode);
			else { // other keys, no special handling is needed
				::chewing_handle_Default(chewingContext_, charCode);
			}
		}
	} else { // non-printable keys
		switch(keyEvent.keyCode()) {
		case VK_ESCAPE:
			::chewing_handle_Esc(chewingContext_);
			break;
		case VK_RETURN:
			::chewing_handle_Enter(chewingContext_);
			break;
		case VK_TAB:
			::chewing_handle_Tab(chewingContext_);
			break;
		case VK_DELETE:
			::chewing_handle_Del(chewingContext_);
			break;
		case VK_BACK:
			::chewing_handle_Backspace(chewingContext_);
			break;
		case VK_UP:
			::chewing_handle_Up(chewingContext_);
			break;
		case VK_DOWN:
			::chewing_handle_Down(chewingContext_);
			break;
		case VK_LEFT:
			::chewing_handle_Left(chewingContext_);
			break;
		case VK_RIGHT:
			::chewing_handle_Right(chewingContext_);
			break;
		case VK_HOME:
			::chewing_handle_Home(chewingContext_);
			break;
		case VK_END:
			::chewing_handle_End(chewingContext_);
			break;
		case VK_PRIOR:
			::chewing_handle_PageUp(chewingContext_);
			break;
		case VK_NEXT:
			::chewing_handle_PageDown(chewingContext_);
			break;
		}
	}

	updateLangButtons();

	if(::chewing_keystroke_CheckIgnore(chewingContext_))
		return false;

	// handle candidates
	if(hasCandidates()) {
		if(!showingCandidates())
			showCandidates(session);
		else
			updateCandidates(session);
	}
	else {
		if(showingCandidates())
			hideCandidates();
	}

	// has something to commit
	if(::chewing_commit_Check(chewingContext_)) {
		if(!isComposing()) // start the composition
			startComposition(session->context());

		char* buf = ::chewing_commit_String(chewingContext_);
		int len;
		wchar_t* wbuf = utf8ToUtf16(buf, &len);
		::chewing_free(buf);
		// commit the text, replace currently selected text with our commit string
		setCompositionString(session, wbuf, len);
		delete []wbuf;

		if(isComposing())
			endComposition(session->context());
	}

	wstring compositionBuf;
	if(::chewing_buffer_Check(chewingContext_)) {
		char* buf = ::chewing_buffer_String(chewingContext_);
		int len;
		wchar_t* wbuf;
		if(buf) {
			wbuf = ::utf8ToUtf16(buf, &len);
			::chewing_free(buf);
			compositionBuf += wbuf;
			delete []wbuf;
		}
	}

	if(!::chewing_zuin_Check(chewingContext_)) {
		int zuinNum;
		char* buf = ::chewing_zuin_String(chewingContext_, &zuinNum);
		if(buf) {
			int len;
			wchar_t* wbuf = ::utf8ToUtf16(buf, &len);
			::chewing_free(buf);
			compositionBuf += wbuf;
			delete []wbuf;
		}
	}

	// has something in composition buffer
	if(!compositionBuf.empty()) {
		if(!isComposing()) { // start the composition
			startComposition(session->context());
		}
		setCompositionString(session, compositionBuf.c_str(), compositionBuf.length());
	}
	else { // nothing left in composition buffer, terminate composition status
		if(isComposing())
			endComposition(session->context());
	}

	// update cursor pos
	if(isComposing()) {
		setCompositionCursor(session, ::chewing_cursor_Current(chewingContext_));
	}
/*
	Ime::ComQIPtr<ITfInsertAtSelection> sel = session->context();
	if(sel) {
		Ime::ComPtr<ITfRange> range;
		sel->InsertTextAtSelection(session->editCookie(), 0, L"TEXT", 4, &range);
	}
*/
	return true;
}

// virtual
bool TextService::filterKeyUp(Ime::KeyEvent& keyEvent) {
	return false;
}

// virtual
bool TextService::onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	return true;
}

// virtual
bool TextService::onPreservedKey(const GUID& guid) {
	// some preserved keys registered in ctor are pressed
	if(::IsEqualIID(guid, g_shiftSpaceGuid)) { // shift + space is pressed
		if(chewingContext_) {
			::chewing_set_ShapeMode(chewingContext_, !shapeMode_);
			updateLangButtons();
		}
		return true;
	}
	else if(::IsEqualGUID(guid, g_shiftUpGuid)) { // shift alone, key up
		// FIXME: this event is also fired when Shift + <other keys>
		// is pressed and then released.
		// we have to detect if only shift key along is pressed and then released
		// and no other key events happened during keyDown and keyUp.
		return false;
	}
	return false;
}


// virtual
bool TextService::onCommand(UINT id) {
	switch(id) {
	case ID_SWITCH_LANG:
		// TODO: switch between Chinses and English modes
		// switchLangButton_->setIcon(IDI_ENG);
		break;
	case ID_SWITCH_SHAPE:
		// TODO: switch between half shape and full shape modes
		// switchShapeButton_->setIcon(IDI_FULL_SHAPE);
		break;
	case ID_CONFIG: // show config dialog
		if(!isImmersive()) { // only do this in desktop app mode
			onConfigure(HWND_DESKTOP);
		}
		break;
	case ID_ABOUT: // show about dialog
		if(!isImmersive()) { // only do this in desktop app mode
			Ime::Dialog dlg;
			dlg.showModal(this->imeModule()->hInstance(), IDD_ABOUT);
	    }
		break;
	case ID_WEBSITE: // visit chewing website
		::ShellExecuteW(NULL, NULL, L"http://chewing.im/", NULL, NULL, SW_SHOWNORMAL);
		break;
	case ID_GROUP: // visit chewing google groups website
		::ShellExecuteW(NULL, NULL, L"http://groups.google.com/group/chewing-devel", NULL, NULL, SW_SHOWNORMAL);
		break;
	case ID_BUGREPORT: // visit bug tracker page
		::ShellExecuteW(NULL, NULL, L"http://code.google.com/p/chewing/issues/list", NULL, NULL, SW_SHOWNORMAL);
		break;
	case ID_MOEDICT: // a very awesome online Chinese dictionary
		::ShellExecuteW(NULL, NULL, L"https://www.moedict.tw/", NULL, NULL, SW_SHOWNORMAL);
		break;
	case ID_DICT: // online Chinese dictonary
		::ShellExecuteW(NULL, NULL, L"http://dict.revised.moe.edu.tw/", NULL, NULL, SW_SHOWNORMAL);
		break;
	case ID_SIMPDICT: // a simplified version of the online dictonary
		::ShellExecuteW(NULL, NULL, L"http://dict.concised.moe.edu.tw/main/cover/main.htm", NULL, NULL, SW_SHOWNORMAL);
		break;
	case ID_LITTLEDICT: // a simplified dictionary for little children
		::ShellExecuteW(NULL, NULL, L"http://dict.mini.moe.edu.tw/cgi-bin/gdic/gsweb.cgi?o=ddictionary", NULL, NULL, SW_SHOWNORMAL);
		break;
	case ID_PROVERBDICT: // a dictionary for proverbs (seems to be broken at the moment?)
		::ShellExecuteW(NULL, NULL, L"http://dict.idioms.moe.edu.tw/?", NULL, NULL, SW_SHOWNORMAL);
		break;
	default:
		return false;
	}
	return true;
}

// virtual
bool TextService::onConfigure(HWND hwndParent) {
	// FIXME: alternatively, should we make the configuration
	//        dialog a separate program and launch it instead?

	// FIXME: something wrong causing crashes here.
	// I'm not sure what's the problem yet.
	Ime::PropertyDialog dlg;
	TypingPage* typingPage = new TypingPage();
	dlg.addPage(typingPage);
	dlg.showModal(this->imeModule()->hInstance(), (LPCTSTR)IDS_CONFIG_TITLE, 0, hwndParent);
	return true;
}


void TextService::updateCandidates(Ime::EditSession* session) {
	assert(candidateWindow_);
	candidateWindow_->clear();

	::chewing_cand_Enumerate(chewingContext_);
	int n = ::chewing_cand_ChoicePerPage(chewingContext_);
	for(; n > 0 && ::chewing_cand_hasNext(chewingContext_); --n) {
		char* str = ::chewing_cand_String(chewingContext_);
		wchar_t* wstr = utf8ToUtf16(str);
		::chewing_free(str);
		candidateWindow_->add(wstr);
		delete []wstr;
	}
	candidateWindow_->recalculateSize();
	candidateWindow_->refresh();

	RECT textRect;
	// get the position of composition area from TSF
	if(selectionRect(session, &textRect)) {
		// FIXME: where should we put the candidate window?
		candidateWindow_->move(textRect.left, textRect.bottom);
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
	if(!candidateWindow_) {
		candidateWindow_ = new Ime::CandidateWindow(this, session);
	}
	updateCandidates(session);
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

void TextService::updateLangButtons() {
	if(!chewingContext_)
		return;

	int langMode = ::chewing_get_ChiEngMode(chewingContext_);
	if(langMode != langMode_) {
		langMode_ = langMode;
		switchLangButton_->setIcon(langMode == CHINESE_MODE ? IDI_CHI : IDI_ENG);
	}

	int shapeMode = ::chewing_get_ShapeMode(chewingContext_);
	if(shapeMode != shapeMode_) {
		shapeMode_ = shapeMode;
		switchShapeButton_->setIcon(shapeMode == FULLSHAPE_MODE ? IDI_FULL_SHAPE : IDI_HALF_SHAPE);
	}
}
