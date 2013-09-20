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

#ifndef IME_CANDIDATE_WINDOW_H
#define IME_CANDIDATE_WINDOW_H

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

	int candPerRow() const {
		return candPerRow_;
	}
	void setCandPerRow(int n);

	void recalculateSize();

protected:
	LRESULT wndProc(UINT msg, WPARAM wp , LPARAM lp);
	void onPaint(WPARAM wp, LPARAM lp);
	// void paintItem(wchar_t selKey, std::wstring& str);

private:
	int selKeyWidth_;
	int textWidth_;
	int itemHeight_;
	int candPerRow_;

	std::vector<wchar_t> selKeys_;
	std::vector<std::wstring> items_;
};

}

#endif
