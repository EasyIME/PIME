#ifndef _PIME_LAUNCHER_UTILS_H_
#define _PIME_LAUNCHER_UTILS_H_

#include <json/json.h>

bool loadJsonFile(const std::wstring filename, Json::Value& result);

bool saveJsonFile(const std::wstring filename, Json::Value& data);

#endif // _PIME_LAUNCHER_UTILS_H_
