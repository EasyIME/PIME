#include <fstream>
#include "Utils.h"

bool loadJsonFile(const std::wstring filename, Json::Value& result) {
	std::ifstream fp(filename, std::ifstream::binary);
	if (fp) {
		fp >> result;
		return true;
	}
	return false;
}

bool saveJsonFile(const std::wstring filename, Json::Value& data) {
	std::ofstream fp(filename, std::ifstream::binary);
	if (fp) {
		fp << data;
		return true;
	}
	return false;
}
