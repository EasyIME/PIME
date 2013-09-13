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
		font_ = f;
	}

	const std::vector<std::wstring>& items() const {
		return items_;
	}

	void setItems(const std::vector<std::wstring>& items, const std::vector<wchar_t>& sekKeys) {
		items_ = items;
		selKeys_ = selKeys_;
		recalculateSize();
		refresh();
	}

	void add(std::wstring item, wchar_t selKey) {
		items_.push_back(item);
		selKeys_.push_back(selKey);
	}

	void clear() {
		items_.clear();
		selKeys_.clear();
	}

	void recalculateSize();
	void updateFont();

protected:
	LRESULT wndProc(UINT msg, WPARAM wp , LPARAM lp);
	void onPaint(WPARAM wp, LPARAM lp);

private:
	HFONT font_;
	int fontSize_;
	int margin_;
	int spacing_;
	int selKeyWidth_;

	std::vector<wchar_t> selKeys_;
	std::vector<std::wstring> items_;
	bool isImmersive_;
};

}
