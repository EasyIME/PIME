//
//	Copyright (C) 2026 The PIME Developers
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
//	Generated with assistance from Antigravity.
//

#pragma once

#include <nlohmann/json.hpp>
#include <string>
#include <type_traits>
#include <utility>

namespace PIME {

/// Exception-free helpers to access and parse JSON data with nlohmann/json.
///
/// Why avoid try/catch in PIMETextService:
/// By default, the nlohmann/json library relies heavily on C++ exceptions (try/catch)
/// for error reporting (e.g., parse errors, type mismatches, and .value() on non-objects).
/// However, we cannot rely on C++ exceptions in text services because:
///  1. PIMETextService runs in-process inside arbitrary host applications (games,
///     sandboxed browsers, applications built without MSVC CRT or exception tables).
///  2. On Windows, C++ exceptions raise Win32 SEH code 0xE06D7363; anti-cheat engines,
///     low-integrity sandboxes, or missing unwind tables in host hooks can turn
///     an ordinary C++ throw into an immediate, uncatchable process crash.
///  3. C++ exceptions must never cross COM / TSF ABI boundaries.
///
/// Therefore, all utilities here are marked noexcept and use non-throwing type checks
/// and parse variants so malformed JSON never triggers a crash.

/// Safe accessor for JSON object fields. Returns defaultValue without throwing when:
///  - obj is not an object (e.g. array, null, number)
///  - key is missing
///  - the value type doesn't match T
///
/// Uses is_*() + get() internally so no C++ exceptions are ever thrown.
template <typename T>
T jsonValueOr(const nlohmann::json& obj, const char* key, const T& defaultValue) noexcept {
	if (!obj.is_object()) {
		return defaultValue;
	}
	auto it = obj.find(key);
	if (it == obj.end()) {
		return defaultValue;
	}

	if constexpr (std::is_same_v<T, std::string>) {
		if (it->is_string()) {
			return it->get_ref<const std::string&>();
		}
	} else if constexpr (std::is_same_v<T, bool>) {
		if (it->is_boolean()) {
			return it->get<bool>();
		}
	} else if constexpr (std::is_arithmetic_v<T>) {
		// is_number() covers integer, unsigned, and float JSON values.
		// get<T>() performs a safe static_cast between numeric subtypes.
		if (it->is_number()) {
			return it->get<T>();
		}
	}
	return defaultValue;
}

/// Overload for string literals / const char* to return std::string safely.
inline std::string jsonValueOr(const nlohmann::json& obj, const char* key, const char* defaultValue) noexcept {
	return jsonValueOr<std::string>(obj, key, std::string(defaultValue ? defaultValue : ""));
}

/// Parse JSON without throwing exceptions. Returns a discarded value on syntax error.
template <typename InputType>
inline nlohmann::json parseJsonNoThrow(InputType&& input) noexcept {
	return nlohmann::json::parse(std::forward<InputType>(input), /*callback=*/nullptr, /*allow_exceptions=*/false);
}

} // namespace PIME
