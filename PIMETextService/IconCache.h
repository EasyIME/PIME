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

#ifndef PIME_ICON_CACHE_H
#define PIME_ICON_CACHE_H

#include <windows.h>
#include <string>
#include <unordered_map>
#include <mutex>

namespace PIME {

class IconCache {
public:
	IconCache();
	~IconCache();

	IconCache(const IconCache&) = delete;
	IconCache& operator=(const IconCache&) = delete;

	HICON getIcon(const std::wstring& filePath);
	void clear();

private:
	std::mutex mutex_;
	std::unordered_map<std::wstring, HICON> cache_;
};

} // namespace PIME

#endif // PIME_ICON_CACHE_H
