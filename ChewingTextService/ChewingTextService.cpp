#include "ChewingTextService.h"
#include <assert.h>
#include <string>
#include <libIME/Utils.h>
#include <libIME/LangBarButton.h>
#include "ChewingImeModule.h"
#include "resource.h"

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

TextService::TextService(ImeModule* module):
	Ime::TextService(module),
	showingCandidates_(false),
	candidateWindow_(NULL),
	chewingContext_(NULL) {

	// add language bar buttons
	// siwtch Chinese/English modes
	Ime::LangBarButton* button = new Ime::LangBarButton(this, g_modeButtonGuid);
	button->setTooltip(IDS_SWITCH_LANG);
	button->setIcon(IDI_CHI);
	addButton(button);
	button->Release();

	// toggle full shape/half shape
	button = new Ime::LangBarButton(this, g_shapeTypeButtonGuid);
	button->setTooltip(IDS_SWITCH_SHAPE);
	button->setIcon(IDI_HALF_SHAPE);
	addButton(button);
	button->Release();

	// settings and others, may open a popup menu
	button = new Ime::LangBarButton(this, g_settingsButtonGuid);
	button->setTooltip(IDS_SETTINGS);
	button->setIcon(IDI_CONFIG);
	HMENU menu = ::LoadMenuW(this->module()->hInstance(), LPCTSTR(IDR_MENU));
	HMENU popup = ::GetSubMenu(menu, 0);
	button->setMenu(popup);
	addButton(button);
	button->Release();
}

TextService::~TextService(void) {
	if(candidateWindow_)
		delete candidateWindow_;

	if(chewingContext_)
		::chewing_delete(chewingContext_);
}

// virtual
void TextService::onActivate() {
	if(!chewingContext_) {
		chewingContext_ = ::chewing_new();
		::chewing_set_maxChiSymbolLen(chewingContext_, 50);
	}
	if(!candidateWindow_) {
		candidateWindow_ = new Ime::CandidateWindow();
	}
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
	assert(chewingContext_);
	// TODO: check if we're in Chinses or English mode
	if(!isComposing()) {
		// when not composing, we only cares about Bopomopho
		// FIXME: we should check if the key is mapped to a phonetic symbol instead
		// FIXME: we need to handle Shift, Alt, and Ctrl, ...etc.
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
	/*
	 * FIXME: the following keys are not handled:
	 * shift left		VK_LSHIFT
	 * shift right		VK_RSHIFT
	 * caps lock		VK_CAPITAL
	 * ctrl num
	 * shift space
	 * numlock num		VK_NUMLOCK
	 */

	Ime::KeyState shiftState(VK_SHIFT);
	// set this to true or false according to the status of Shift key
	::chewing_set_easySymbolInput(chewingContext_, shiftState.isDown());

	UINT charCode = keyEvent.charCode();
	if(charCode && isgraph(charCode) && !keyEvent.isExtended()) { // printable characters (exclude extended keys?)
		// FIXME: should we treat numpad keys differently?
		if(isalpha(charCode))
			::chewing_handle_Default(chewingContext_, tolower(charCode));
		else
			::chewing_handle_Default(chewingContext_, charCode);
	} else {
		switch(keyEvent.keyCode()) {
		case VK_SPACE:
			::chewing_handle_Space(chewingContext_);
			break;
		case VK_ESCAPE:
			::chewing_handle_Esc(chewingContext_);
			break;
		case VK_RETURN:
			::chewing_handle_Enter(chewingContext_);
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
		default:
			return S_OK;
		}
	}

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
bool TextService::onCommand(UINT id) {
	switch(id) {
	case ID_ABOUT:
		// TODO: show about dialog
		break;
	default:
		return false;
	}
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
	assert(candidateWindow_);

	updateCandidates(session);
	candidateWindow_->show();
	showingCandidates_ = true;
}

// hide candidate list window
void TextService::hideCandidates() {
	assert(candidateWindow_);

	candidateWindow_->hide();
	candidateWindow_->clear();
	showingCandidates_ = false;
}
