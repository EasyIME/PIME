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
#include "JsonUtils.h"
#include "PIMETextService.h"
#include <algorithm>
#include <string>
#include <fstream>
#include <cstring>
#include <ShlObj.h>
#include <Shellapi.h>
#include <Shlwapi.h>
#include <nlohmann/json.hpp>
#include "../libIME2/src/Utils.h"
#include "../libIME2/src/DisplayAttributeInfo.h"

using json = nlohmann::json;

namespace PIME {

namespace {
// CLSID of our Text service
// {35F67E9D-A54D-4177-9697-8B0AB71A9E04}
const GUID g_textServiceClsid = 
{ 0x35f67e9d, 0xa54d, 0x4177, { 0x96, 0x97, 0x8b, 0xa, 0xb7, 0x1a, 0x9e, 0x4 } };

// {53BCC437-ED0E-4D7D-9B46-57CAB8A9F255}
static const GUID g_inputDisplayAttributeGuid = 
{ 0x53bcc437, 0xed0e, 0x4d7d, { 0x9b, 0x46, 0x57, 0xca, 0xb8, 0xa9, 0xf2, 0x55 } };

static std::vector<Ime::ComPtr<Ime::DisplayAttributeInfo>> createDisplayAttrInfos() {
    auto inputAttrib = Ime::ComPtr<Ime::DisplayAttributeInfo>::make(g_inputDisplayAttributeGuid);
    inputAttrib->setLineStyle(TF_LS_DOT);
	return {std::move(inputAttrib)};
}

}

ImeModule::ImeModule(HMODULE module):
	Ime::ImeModule(module, g_textServiceClsid, createDisplayAttrInfos()) {
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

		// load backend information
		std::ifstream fp(programDir_ + L"\\backends.json", std::ifstream::binary);
		if (fp) {
			json backendsInfo = parseJsonNoThrow(fp);
			if (backendsInfo.is_array()) {
				for (const auto& backend: backendsInfo) {
					if (!backend.is_object()) {
						continue;
					}
					std::string nameUtf8 = jsonValueOr<std::string>(backend, "name", "");
					if (!nameUtf8.empty()) {
						std::wstring name = utf8ToUtf16(nameUtf8.c_str());
						backendDirs_.push_back(name);
					}
				}
			}
		}
	}
}

ImeModule::~ImeModule(void) {
}

// virtual
Ime::TextService* ImeModule::createTextService() {
	TextService* service = new PIME::TextService(this);
	return service;
}

static std::vector<std::wstring> listSubdirs(const std::wstring& dir) {
	std::vector<std::wstring> subdirs;
	WIN32_FIND_DATAW findData = { 0 };
	HANDLE hFind = ::FindFirstFileW((dir + L"\\*").c_str(), &findData);
	if (hFind != INVALID_HANDLE_VALUE) {
		do {
			if ((findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) && findData.cFileName[0] != L'.') {
				subdirs.push_back(dir + L'\\' + findData.cFileName);
			}
		} while (::FindNextFileW(hFind, &findData));
		::FindClose(hFind);
	}
	std::sort(subdirs.begin(), subdirs.end());
	return subdirs;
}

std::vector<ImeModule::ImeManifest> ImeModule::findImeManifests() const {
	std::vector<ImeManifest> manifests;
	for (const auto& backendDir : backendDirs_) {
		const std::wstring inputMethodsDir = programDir_ + L'\\' + backendDir + L"\\input_methods";
		for (const auto& moduleDir : listSubdirs(inputMethodsDir)) {
			std::wstring rootJson = moduleDir + L"\\ime.json";
			if (::GetFileAttributesW(rootJson.c_str()) != INVALID_FILE_ATTRIBUTES) {
				manifests.push_back({std::move(rootJson), moduleDir});
			}
			for (const auto& profileDir : listSubdirs(moduleDir + L"\\ime_profiles")) {
				std::wstring profileJson = profileDir + L"\\ime.json";
				if (::GetFileAttributesW(profileJson.c_str()) != INVALID_FILE_ATTRIBUTES) {
					manifests.push_back({std::move(profileJson), moduleDir});
				}
			}
		}
	}
	return manifests;
}

bool ImeModule::loadImeInfo(const std::string& guid, std::wstring& moduleDir, json& content) {
	for (const auto& manifest : findImeManifests()) {
		std::ifstream fp(manifest.jsonPath, std::ifstream::binary);
		if (!fp) {
			continue;
		}
		content = parseJsonNoThrow(fp);
		if (!content.is_object() || content.is_discarded()) {
			continue;
		}
		std::string imeGuid = jsonValueOr<std::string>(content, "guid", "");
		if (stricmp(guid.c_str(), imeGuid.c_str()) == 0) {
			// found the language profile
			moduleDir = manifest.moduleDir;
			return true;
		}
	}
	return false;
}

// virtual
bool ImeModule::onConfigure(HWND hwndParent, LANGID langid, REFGUID rguidProfile) {
	// FIXME: this is inefficient. Should we cache known modules?
	LPOLESTR pGuidStr = NULL;
	if (FAILED(::StringFromCLSID(rguidProfile, &pGuidStr)))
		return false;
	std::string guidStr = utf16ToUtf8(pGuidStr);
	CoTaskMemFree(pGuidStr);

	std::wstring configCommand;
	std::wstring configParams;
	std::wstring configDir;

	// find the input method module
	std::wstring moduleDir;
	json info;
	if (loadImeInfo(guidStr, moduleDir, info)) {
		// relative paths are resolved against the IME module dir
		std::wstring currentDir = moduleDir + L'\\';
		configCommand = utf8ToUtf16(jsonValueOr<std::string>(info, "configTool", "").c_str());
		configParams = utf8ToUtf16(jsonValueOr<std::string>(info, "configToolParams", "").c_str());
		configDir = utf8ToUtf16(jsonValueOr<std::string>(info, "configToolDir", "").c_str());
		// for some mysterious reasons, relative paths do not work here (according to Win32 API doc it should work).
		if (PathIsRelative(configCommand.c_str())) {  // convert it to an absolute path
			wchar_t absPath[MAX_PATH];
			PathCanonicalize(absPath, (currentDir + configCommand).c_str());
			configCommand = absPath;
		}
		if (!configDir.empty()) {
			if (PathIsRelative(configDir.c_str())) {  // convert it to an absolute path
				wchar_t absPath[MAX_PATH];
				PathCanonicalize(absPath, (currentDir + configDir).c_str());
				configDir = absPath;
			}
		}
	}

	if (!configCommand.empty()) { // command line is found
		// execute the config tool
		::ShellExecuteW(hwndParent, L"open", 
			configCommand.c_str(),
			configParams.empty() ? NULL : configParams.c_str(),
			configDir.empty() ? NULL : configDir.c_str(),
			SW_SHOWNORMAL);
	}
	else {
		// FIXME: this message should be localized.
		::MessageBoxW(hwndParent, L"The input module does not have a config tool.", NULL, MB_OK);
	}
	return true;
}


} // namespace PIME
