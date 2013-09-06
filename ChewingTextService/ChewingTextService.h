#ifndef CHEWING_TEXT_SERVICE_H
#define CHEWING_TEXT_SERVICE_H

#include <LibIME/TextService.h>
#include <LibIME/CandidateWindow.h>
#include <LibIME/EditSession.h>
#include <chewing.h>

namespace Chewing {

class TextService: public Ime::TextService {
public:
	TextService(void);
	virtual ~TextService(void);

	virtual void onActivate();
	virtual void onDeactivate();

	virtual void onFocus();

	virtual bool filterKeyDown(long key);
	virtual bool onKeyDown(long key, Ime::EditSession* session);
	virtual bool filterKeyUp(long key);
	virtual bool onKeyUp(long key, Ime::EditSession* session);

	ChewingContext* chewingContext() {
		return chewingContext_;
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

private:
	ChewingContext* chewingContext_;
	Ime::CandidateWindow* candidateWindow_;
	bool showingCandidates_;
};

}

#endif
