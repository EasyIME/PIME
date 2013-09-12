#pragma once

#include "ImeWindow.h"
#include <string>
#include <vector>

namespace Ime {

class TextService;
class EditSession;

// TODO: make the candidate window looks different in immersive mode
class CandidateWindow : public ImeWindow {
public:
	CandidateWindow(TextService* service, EditSession* session);
	~CandidateWindow(void);

	void setFont(HFONT f){
		font = f;
	}

	const std::vector<std::wstring>& items() const {
		return items_;
	}

	void setItems(const std::vector<std::wstring>& items) {
		items_ = items;
		recalculateSize();
		refresh();
	}

	void add(std::wstring item) {
		items_.push_back(item);
	}

	void clear() {
		items_.clear();
	}

	void recalculateSize();
    void updateFont();

protected:
	LRESULT wndProc(UINT msg, WPARAM wp , LPARAM lp);
	void onPaint(WPARAM wp, LPARAM lp);

private:
    HFONT font;
    int   font_size;
	std::vector<std::wstring> items_;
	bool isImmersive_;
};

}
