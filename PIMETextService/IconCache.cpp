//
//	Copyright (C) 2013-2026 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

#include "IconCache.h"

namespace PIME {

IconCache::IconCache() = default;

IconCache::~IconCache() {
	clear();
}

HICON IconCache::getIcon(const std::wstring& filePath) {
	if (filePath.empty()) {
		return NULL;
	}
	std::lock_guard<std::mutex> lock(mutex_);
	auto it = cache_.find(filePath);
	if (it != cache_.end()) {
		return it->second;
	}

	HICON hIcon = (HICON)::LoadImageW(NULL, filePath.c_str(), IMAGE_ICON, 0, 0, LR_DEFAULTCOLOR | LR_LOADFROMFILE);
	if (hIcon) {
		cache_[filePath] = hIcon;
	}
	return hIcon;
}

void IconCache::clear() {
	std::lock_guard<std::mutex> lock(mutex_);
	for (auto& pair : cache_) {
		if (pair.second) {
			::DestroyIcon(pair.second);
		}
	}
	cache_.clear();
}

} // namespace PIME
