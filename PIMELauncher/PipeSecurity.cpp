#include "PipeSecurity.h"

#include <AclAPI.h>
#include <sddl.h>
#include <VersionHelpers.h>

#include <string>
#include <stdexcept>

#define PROCESS_ALL_ACCESS_HEX  TEXT("0x1fffff")  // hex string of PROCESS_ALL_ACCESS


namespace PIME {

static std::wstring sidToStr(PSID sid) {
    std::wstring sidStr;
    LPWSTR buf = nullptr;
    if (::ConvertSidToStringSidW(sid, &buf)) {
        sidStr = buf;
        ::LocalFree(buf);
    }
    return sidStr;
}


static std::wstring getLogonSid() {
    // Get process token with TOKEN_QUERY privilege.
    std::wstring logonSidStr;
    HANDLE processToken = INVALID_HANDLE_VALUE;
    try {
        if (!::OpenProcessToken(::GetCurrentProcess(), TOKEN_QUERY, &processToken)) {
            throw std::runtime_error("Fail to open process token");
        }

        DWORD bufSize = 0;
        if (!::GetTokenInformation(processToken, TokenGroups, nullptr, 0, &bufSize)) {
            if (::GetLastError() != ERROR_INSUFFICIENT_BUFFER) {
                throw std::runtime_error("Fail to get token info buffer size.");
            }
        }

        auto tokenGroupsBuf = std::make_unique<char[]>(bufSize);
        if (!::GetTokenInformation(processToken, TokenGroups, tokenGroupsBuf.get(), bufSize, &bufSize)) {
            DWORD err = ::GetLastError();
            throw std::runtime_error("Fail to get token group data.");
        }

        auto groups = reinterpret_cast<TOKEN_GROUPS*>(tokenGroupsBuf.get());
        PSID logonSid = nullptr;
        for (DWORD i = 0; i < groups->GroupCount; ++i) {
            auto group = groups->Groups[i];
            if ((group.Attributes & SE_GROUP_LOGON_ID) == SE_GROUP_LOGON_ID) {
                /// Found the logon group.
                logonSid = group.Sid;
                break;
            }
        }

        if (logonSid) {
            logonSidStr = sidToStr(logonSid);
        }
    }
    catch (...) {
        if (processToken != INVALID_HANDLE_VALUE) {
            ::CloseHandle(processToken);
        }
    }
    return logonSidStr;
}

static bool getProcessOwnerSids(std::wstring& ownerSidStr, std::wstring& groupSidStr) {
    PSID ownerSid = nullptr;
    PSID groupSid = nullptr;
    PSECURITY_DESCRIPTOR sd = nullptr;
    DWORD ret = ::GetSecurityInfo(::GetCurrentProcess(),
        SE_KERNEL_OBJECT, OWNER_SECURITY_INFORMATION | GROUP_SECURITY_INFORMATION,
        &ownerSid, &groupSid, nullptr, nullptr, &sd);
    if (ret == ERROR_SUCCESS) {
        // FIXME: Do we need to free the SIDs here?
        ownerSidStr = sidToStr(ownerSid);
        groupSidStr = sidToStr(groupSid);
        ::LocalFree(sd);
        return true;
    }
    return false;
}

PipeSecurityAttributes::PipeSecurityAttributes():
    securittyDescriptor_(nullptr) {

    securityAttributes_.nLength = sizeof(SECURITY_ATTRIBUTES);
    securityAttributes_.lpSecurityDescriptor = nullptr;
    securityAttributes_.bInheritHandle = TRUE;

    // References:
    // google-input-tools:
    // https://chromium.googlesource.com/external/google-input-tools/+/master/client/common/security_util_win.cc
    // Windows ACL examples:
    // https://www.installsetupconfig.com/win32programming/accesscontrollistaclexample3_4.html

    auto logonSid = getLogonSid();
    if (logonSid.empty()) {
        return;
    }

    std::wstring ownerSid, groupSid;
    if (!getProcessOwnerSids(ownerSid, groupSid)) {
        return;
    }

    // Use Windows SDDL syntax to describe the security settings.

    std::wstring securityDescriptorStr;
    // owner and group.
    securityDescriptorStr += SDDL_OWNER L":" + ownerSid;
    securityDescriptorStr += SDDL_GROUP L":" + groupSid;

    // DACL
    securityDescriptorStr += SDDL_DACL L":";

    // ACE strings in this DACL.
    // Syntax: ace_type;ace_flags;rights;object_guid;inherit_object_guid;account_sid;(resource_attribute)
    if (::IsWindows8OrGreater()) {
        // Deny Remote Acccess.
        securityDescriptorStr += L"(" SDDL_ACCESS_DENIED L";;" SDDL_GENERIC_ALL L";;;" SDDL_NETWORK L")";

        // Allow general access to LocalSystem.
        securityDescriptorStr += L"(" SDDL_ACCESS_ALLOWED L";;" SDDL_GENERIC_ALL L";;;" SDDL_LOCAL_SYSTEM L")";

        // Allow general access to Built-in Administorators.
        securityDescriptorStr += L"(" SDDL_ACCESS_ALLOWED L";;" SDDL_GENERIC_ALL L";;;" SDDL_BUILTIN_ADMINISTRATORS L")";

        // Allow general access to ALL APPLICATION PACKAGES.
        securityDescriptorStr += L"(" SDDL_ACCESS_ALLOWED L";;" SDDL_GENERIC_ALL L";;;" SDDL_ALL_APP_PACKAGES L")";
    }

    // Add generic & standand and all other possible object specific access right to logon user.

    // Hex of PROCESS_ALL_ACCESS = 0x1ffff
    securityDescriptorStr += L"(" SDDL_ACCESS_ALLOWED L";;" PROCESS_ALL_ACCESS_HEX L";;;" + logonSid + L")";

    // Add low integrity label to support application environment like IE
    // protective mode if system supports(vista or latter).
    if (::IsWindowsVistaOrGreater()) {
        // Reference: https://flylib.com/books/en/1.286.1.27/1/
        // SDDL_MANDATORY_LABEL: Integrity label
        // SDDL_ML_LOW: Low mandatory level.
        // Processes with integrity level lower than "LOW" cannot write to or read from our process.
        securityDescriptorStr += SDDL_SACL L":(" SDDL_MANDATORY_LABEL L";;" SDDL_NO_WRITE_UP SDDL_NO_READ_UP L";;;" SDDL_ML_LOW L")";
    }

    // Convert the string to a security descriptor.
    if (::ConvertStringSecurityDescriptorToSecurityDescriptor(
        securityDescriptorStr.c_str(), SDDL_REVISION_1, &securittyDescriptor_, nullptr)) {
        securityAttributes_.lpSecurityDescriptor = securittyDescriptor_;
    }
}

PipeSecurityAttributes::~PipeSecurityAttributes() {
    if (securittyDescriptor_ != nullptr) {
        ::LocalFree(securittyDescriptor_);
    }
}

} // namespace PIME
