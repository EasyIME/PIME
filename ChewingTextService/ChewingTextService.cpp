#include "ChewingTextService.h"
#include <assert.h>
#include <string>
#include <libIME/Utils.h>

using namespace Chewing;
using namespace std;

TextService::TextService(void):
	chewingContext_(NULL) {
}

TextService::~TextService(void) {
	if(chewingContext_)
		chewing_delete(chewingContext_);
}

// virtual
void TextService::onActivate() {
	if(!chewingContext_) {
		chewingContext_ = chewing_new();
		chewing_set_maxChiSymbolLen(chewingContext_, 50);
	}
}

// virtual
void TextService::onDeactivate() {
	if(chewingContext_) {
		chewing_delete(chewingContext_);
		chewingContext_ = NULL;
	}
}

// virtual
void TextService::onFocus() {
}

#include <iostream>

// virtual
bool TextService::onKeyDown(long key, Ime::EditSession* session) {
	assert(chewingContext_);
    /*
     * FIXME: the following keys are not handled:
     * shift left		VK_LSHIFT
     * shift right		VK_RSHIFT
     * caps lock		VK_CAPITAL
     * page up			VK_PRIOR
     * page down		VK_NEXT
     * ctrl num
     * shift space
     * numlock num		VK_NUMLOCK
	 */
    if('A' <= key && key <= 'Z') {
        chewing_handle_Default(chewingContext_, key - 'A' + 'a');
    } else if ('0' <= key && key <= '9') {
        chewing_handle_Default(chewingContext_, key);
    } else {
        switch(key) {
            case VK_OEM_COMMA:
                chewing_handle_Default(chewingContext_, ',');
                break;
            case VK_OEM_MINUS:
                chewing_handle_Default(chewingContext_, '-');
                break;
            case VK_OEM_PERIOD:
                chewing_handle_Default(chewingContext_, '.');
                break;
            case VK_OEM_1:
                chewing_handle_Default(chewingContext_, ';');
                break;
            case VK_OEM_2:
                chewing_handle_Default(chewingContext_, '/');
                break;
            case VK_OEM_3:
                chewing_handle_Default(chewingContext_, '`');
                break;
            case VK_SPACE:
                chewing_handle_Space(chewingContext_);
                break;
            case VK_ESCAPE:
                chewing_handle_Esc(chewingContext_);
                break;
            case VK_RETURN:
                chewing_handle_Enter(chewingContext_);
                break;
            case VK_DELETE:
                chewing_handle_Del(chewingContext_);
                break;
            case VK_BACK:
                chewing_handle_Backspace(chewingContext_);
                break;
            case VK_UP:
                chewing_handle_Up(chewingContext_);
                break;
            case VK_DOWN:
                chewing_handle_Down(chewingContext_);
            case VK_LEFT:
                chewing_handle_Left(chewingContext_);
                break;
            case VK_RIGHT:
                chewing_handle_Right(chewingContext_);
                break;
            case VK_HOME:
                chewing_handle_Home(chewingContext_);
                break;
            case VK_END:
                chewing_handle_End(chewingContext_);
                break;
            default:
                return S_OK;
        }
    }

	// has something to commit
	if(chewing_commit_Check(chewingContext_)) {
		if(!isComposing()) // start the composition
			startComposition(session);

		char* buf = ::chewing_commit_String(chewingContext_);
		int len;
		wchar_t* wbuf = utf8ToUtf16(buf, &len);
		chewing_free(buf);
		// commit the text, replace currently selected text with our commit string
		replaceSelectedText(session, wbuf, len);
		delete []wbuf;

		if(isComposing())
			endComposition(session);
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
		if(!isComposing()) // start the composition
			startComposition(session);
		replaceSelectedText(session, compositionBuf.c_str(), compositionBuf.length());
	}
	else { // nothing left in composition buffer, terminate composition status
		if(isComposing())
			endComposition(session);
	}

#if 0
    ChewingCandidates candidate(chewingContext_);
	SetCandidates(candidate);

    CImeString commit(chewingContext_, IME_STRING_COMMIT);
    if (!commit.IsEmpty()) {
		CommitString(commit.GetString(), commit.GetLength());
    }

    // Composition is mapped to preedit buffer + zuin buffer
    CImeString preedit_zuin(chewingContext_, IME_STRING_PREEDIT);
	SetComposition(preedit_zuin.GetString(), preedit_zuin.GetLength());
#endif
	return true;
}

// virtual
bool TextService::onKeyUp(long key, Ime::EditSession* session) {
	return true;
}
