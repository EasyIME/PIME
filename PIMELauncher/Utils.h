#ifndef _PIME_LAUNCHER_UTILS_H_
#define _PIME_LAUNCHER_UTILS_H_

#include <nlohmann/json.hpp>
#include <string>

namespace PIME {

bool loadJsonFile(const std::wstring filename, nlohmann::json& result);

bool saveJsonFile(const std::wstring filename, const nlohmann::json& data);

std::wstring getCurrentExecutableDir();

std::wstring getAppLocalDir();

bool makeDirs(const std::wstring& path);

std::string generateUuidStr();

} // namespace PIME

#endif // _PIME_LAUNCHER_UTILS_H_
