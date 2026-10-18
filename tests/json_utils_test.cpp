//
//	Copyright (C) 2026 The PIME Developers
//
//	Generated with assistance from Antigravity.
//

#include "JsonUtils.h"

#include <gtest/gtest.h>
#include <string>

using namespace PIME;
using json = nlohmann::json;

TEST(JsonUtilsTest, ParseJsonNoThrowValid) {
	json j = parseJsonNoThrow("{\"name\": \"test\", \"id\": 42, \"enabled\": true}");
	EXPECT_TRUE(j.is_object());
	EXPECT_FALSE(j.is_discarded());
	EXPECT_EQ(jsonValueOr<std::string>(j, "name", ""), "test");
	EXPECT_EQ(jsonValueOr<int>(j, "id", 0), 42);
	EXPECT_EQ(jsonValueOr<unsigned int>(j, "id", 0u), 42u);
	EXPECT_TRUE(jsonValueOr<bool>(j, "enabled", false));
}

TEST(JsonUtilsTest, ParseJsonNoThrowInvalid) {
	json j = parseJsonNoThrow("{ invalid json ... }");
	EXPECT_TRUE(j.is_discarded());

	json empty = parseJsonNoThrow("");
	EXPECT_TRUE(empty.is_discarded());
}

TEST(JsonUtilsTest, JsonValueOrMissingKey) {
	json j = json::object();
	EXPECT_EQ(jsonValueOr<std::string>(j, "missing_str", "default_val"), "default_val");
	EXPECT_EQ(jsonValueOr<int>(j, "missing_int", 99), 99);
	EXPECT_TRUE(jsonValueOr<bool>(j, "missing_bool", true));
}

TEST(JsonUtilsTest, JsonValueOrTypeMismatch) {
	json j = {
		{"str_as_null", nullptr},
		{"str_as_int", 123},
		{"str_as_arr", json::array({1, 2, 3})},
		{"str_as_obj", json::object({{"k", "v"}})},
		{"int_as_str", "not_a_number"},
		{"bool_as_str", "true"}
	};

	EXPECT_EQ(jsonValueOr<std::string>(j, "str_as_null", "fallback"), "fallback");
	EXPECT_EQ(jsonValueOr<std::string>(j, "str_as_int", "fallback"), "fallback");
	EXPECT_EQ(jsonValueOr<std::string>(j, "str_as_arr", "fallback"), "fallback");
	EXPECT_EQ(jsonValueOr<std::string>(j, "str_as_obj", "fallback"), "fallback");
	EXPECT_EQ(jsonValueOr<int>(j, "int_as_str", -1), -1);
	EXPECT_FALSE(jsonValueOr<bool>(j, "bool_as_str", false));
}

TEST(JsonUtilsTest, JsonValueOrNonObjectRoot) {
	json arr = json::array({1, 2, "hello"});
	EXPECT_EQ(jsonValueOr<std::string>(arr, "name", "def"), "def");
	EXPECT_EQ(jsonValueOr<int>(arr, "id", 0), 0);

	json num = 12345;
	EXPECT_EQ(jsonValueOr<std::string>(num, "name", "def"), "def");

	json str = "just a string";
	EXPECT_EQ(jsonValueOr<std::string>(str, "name", "def"), "def");

	json nullVal = nullptr;
	EXPECT_EQ(jsonValueOr<std::string>(nullVal, "name", "def"), "def");
}

TEST(JsonUtilsTest, NoexceptVerification) {
	json j = json::object();
	static_assert(noexcept(jsonValueOr<std::string>(j, "k", std::string{})), "string overload must be noexcept");
	static_assert(noexcept(jsonValueOr<bool>(j, "k", false)), "bool overload must be noexcept");
	static_assert(noexcept(jsonValueOr<int>(j, "k", 0)), "int overload must be noexcept");
	static_assert(noexcept(jsonValueOr<unsigned int>(j, "k", 0u)), "uint overload must be noexcept");
	static_assert(noexcept(parseJsonNoThrow("")), "parseJsonNoThrow must be noexcept");
	SUCCEED();
}
