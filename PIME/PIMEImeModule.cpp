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

#include "PIMEImeModule.h"
#include "PIMETextService.h"
#include <string>
#include <fstream>
#include <ShlObj.h>
#include <json/json.h>
#include "../libIME/Utils.h"

namespace PIME {

// CLSID of our Text service
// {35F67E9D-A54D-4177-9697-8B0AB71A9E04}
const GUID g_textServiceClsid = 
{ 0x35f67e9d, 0xa54d, 0x4177, { 0x96, 0x97, 0x8b, 0xa, 0xb7, 0x1a, 0x9e, 0x4 } };

const wchar_t* ImeModule::backendDirs_[] = {
	L"python",
	L"node"
};

ImeModule::ImeModule(HMODULE module):
	Ime::ImeModule(module, g_textServiceClsid) {
	wchar_t path[MAX_PATH];
	HRESULT result;
	// get the program data directory
	// try C:\program files (x86) first
	result = ::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILESX86, NULL, 0, path);
	if(result != S_OK) // failed, fall back to C:\program files
		result = ::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILES, NULL, 0, path);
	if(result == S_OK) { // program files folder is found
		programDir_ = path;
		programDir_ += L"\\PIME";
	}
}

ImeModule::~ImeModule(void) {
}

// virtual
Ime::TextService* ImeModule::createTextService() {
	TextService* service = new PIME::TextService(this);
	return service;
}

bool ImeModule::loadImeInfo(const std::string& guid, std::wstring& filePath, Json::Value& content) {
	bool found = false;
	// find the input method module
	for (const auto backendDir : backendDirs_) {
		std::wstring dirPath = programDir_;
		dirPath += backendDir;
		dirPath += L"\\input_methods";
		// scan the dir for lang profile definition files
		WIN32_FIND_DATA findData = { 0 };
		HANDLE hFind = ::FindFirstFile((dirPath + L"\\*").c_str(), &findData);
		if (hFind != INVALID_HANDLE_VALUE) {
			do {
				if (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) { // this is a subdir
					if (findData.cFileName[0] != '.') {
						std::wstring imejson = dirPath;
						imejson += '\\';
						imejson += findData.cFileName;
						imejson += L"\\ime.json";

						std::ifstream fp(imejson, std::ifstream::binary);
						if (fp) {
							content.clear();
							fp >> content;
							if (guid == content["guid"].asString()) {
								// found the language profile
								found = true;
								break;
							}
						}
					}
				}
			} while (::FindNextFile(hFind, &findData));
			CloseHandle(hFind);
		}
		if (found)
			break;
	}
	return found;
}

// virtual
bool ImeModule::onConfigure(HWND hwndParent, LANGID langid, REFGUID rguidProfile) {
	// FIXME: this is inefficient. Should we cache known modules?
	LPOLESTR pGuidStr = NULL;
	if (FAILED(::StringFromCLSID(rguidProfile, &pGuidStr)))
		return false;
	std::string guidStr = utf16ToUtf8(pGuidStr);
	CoTaskMemFree(pGuidStr);

	std::wstring configTool;
	// find the input method module
	std::wstring infoFilePath;
	Json::Value info;
	if (loadImeInfo(guidStr, infoFilePath, info)) {
		std::wstring relPath = utf8ToUtf16(info.get("configTool", "").asCString());
		if (!relPath.empty()) {
			// get the full path of the config tool
			std::wstring imeDir = infoFilePath.substr(0, infoFilePath.length() - 8); // remove "ime.json" from file path
			configTool = imeDir;
			configTool += relPath;
		}
	}

	if (!configTool.empty()) {
		// FIXME: support node.js?
		// check if this is a python program (ends with .py)
		if (configTool.compare(configTool.length() - 3, 3, L".py") == 0) {
			// find our own python 3 runtime.
			std::wstring pythonPath = programDir_ + L"\\python\\python3\\pythonw.exe";
			configTool = (L"\"" + configTool + L"\""); // quote the path to .py file.
			::ShellExecuteW(hwndParent, L"open", pythonPath.c_str(), configTool.c_str(), NULL, SW_SHOWNORMAL);
		}
		else {
			// execute the file directly
			::ShellExecuteW(hwndParent, L"open", configTool.c_str(), NULL, NULL, SW_SHOWNORMAL);
		}
	}
	return true;
}


} // namespace PIME
