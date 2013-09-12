#ifndef CHEWING_TEXT_SERVICE_H
#define CHEWING_TEXT_SERVICE_H

#include <LibIME/TextService.h>
#include <LibIME/CandidateWindow.h>
#include <LibIME/EditSession.h>
#include <LibIME/LangBarButton.h>
#include <chewing.h>
#include "ChewingImeModule.h"

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

	virtual bool onCommand(UINT id);

	// called when config dialog needs to be launched
	virtual bool onConfigure(HWND hwndParent);

	ChewingContext* chewingContext() {
		return chewingContext_;
	}

	Config& config() {
		return static_cast<ImeModule*>(module())->config();
	}

	bool hasCandidates() {
		return ::chewing_cand_TotalChoice(chewingContext_) > 0;
	}

	bool showingCandidates() {
		return showingCandidates_;
	}

	void showCandidates(Ime::EditSession* session);
	void updateCandidates(Ime::EditSession* session);
	void hideCandidates();

	void updateLangButtons();

private:
	ChewingContext* chewingContext_;
	Ime::CandidateWindow* candidateWindow_;
	bool showingCandidates_;

	Ime::LangBarButton* switchLangButton_;
	Ime::LangBarButton* switchShapeButton_;

	int langMode_;
	int shapeMode_;
};

}

#endif
