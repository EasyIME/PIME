#ifndef _UTILS_H_
#define _UTILS_H_

#include <json/json.h>

bool loadJsonFile(const std::wstring filename, Json::Value& result);

#endif // _UTILS_H_
