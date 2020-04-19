#include "PipeSecurity.h"

#include <AclAPI.h>


namespace PIME {

PipeSecurityAttributes::PipeSecurityAttributes():
    securittyDescriptor_(nullptr),
    acl_(nullptr),
    everyoneSID_(nullptr),
    allAppsSID_(nullptr) {
    // create security attributes for the pipe
    // http://msdn.microsoft.com/en-us/library/windows/desktop/hh448449(v=vs.85).aspx
    // define new Win 8 app related constants
    memset(&explicitAccesses_, 0, sizeof(explicitAccesses_));
    // Create a well-known SID for the Everyone group.
    // FIXME: we should limit the access to current user only
    // See this article for details: https://msdn.microsoft.com/en-us/library/windows/desktop/hh448493(v=vs.85).aspx

    SID_IDENTIFIER_AUTHORITY worldSidAuthority = SECURITY_WORLD_SID_AUTHORITY;
    AllocateAndInitializeSid(&worldSidAuthority, 1,
        SECURITY_WORLD_RID, 0, 0, 0, 0, 0, 0, 0, &everyoneSID_);

    // https://services.land.vic.gov.au/ArcGIS10.1/edESRIArcGIS10_01_01_3143/Python/pywin32/PLATLIB/win32/Demos/security/explicit_entries.py

    explicitAccesses_[0].grfAccessPermissions = GENERIC_ALL;
    explicitAccesses_[0].grfAccessMode = SET_ACCESS;
    explicitAccesses_[0].grfInheritance = SUB_CONTAINERS_AND_OBJECTS_INHERIT;
    explicitAccesses_[0].Trustee.pMultipleTrustee = NULL;
    explicitAccesses_[0].Trustee.MultipleTrusteeOperation = NO_MULTIPLE_TRUSTEE;
    explicitAccesses_[0].Trustee.TrusteeForm = TRUSTEE_IS_SID;
    explicitAccesses_[0].Trustee.TrusteeType = TRUSTEE_IS_WELL_KNOWN_GROUP;
    explicitAccesses_[0].Trustee.ptstrName = (LPTSTR)everyoneSID_;

    // FIXME: will this work under Windows 7 and Vista?
    // create SID for app containers
    SID_IDENTIFIER_AUTHORITY appPackageAuthority = SECURITY_APP_PACKAGE_AUTHORITY;
    AllocateAndInitializeSid(&appPackageAuthority,
        SECURITY_BUILTIN_APP_PACKAGE_RID_COUNT,
        SECURITY_APP_PACKAGE_BASE_RID,
        SECURITY_BUILTIN_PACKAGE_ANY_PACKAGE,
        0, 0, 0, 0, 0, 0, &allAppsSID_);

    explicitAccesses_[1].grfAccessPermissions = GENERIC_ALL;
    explicitAccesses_[1].grfAccessMode = SET_ACCESS;
    explicitAccesses_[1].grfInheritance = SUB_CONTAINERS_AND_OBJECTS_INHERIT;
    explicitAccesses_[1].Trustee.pMultipleTrustee = NULL;
    explicitAccesses_[1].Trustee.MultipleTrusteeOperation = NO_MULTIPLE_TRUSTEE;
    explicitAccesses_[1].Trustee.TrusteeForm = TRUSTEE_IS_SID;
    explicitAccesses_[1].Trustee.TrusteeType = TRUSTEE_IS_GROUP;
    explicitAccesses_[1].Trustee.ptstrName = (LPTSTR)allAppsSID_;

    // create DACL
    DWORD err = SetEntriesInAcl(2, explicitAccesses_, NULL, &acl_);
    if (0 == err) {
        // security descriptor
        securittyDescriptor_ = (PSECURITY_DESCRIPTOR)LocalAlloc(LPTR, SECURITY_DESCRIPTOR_MIN_LENGTH);
        InitializeSecurityDescriptor(securittyDescriptor_, SECURITY_DESCRIPTOR_REVISION);

        // Add the ACL to the security descriptor. 
        SetSecurityDescriptorDacl(securittyDescriptor_, TRUE, acl_, FALSE);
    }

    securityAttributes_.nLength = sizeof(SECURITY_ATTRIBUTES);
    securityAttributes_.lpSecurityDescriptor = securittyDescriptor_;
    securityAttributes_.bInheritHandle = TRUE;
}

PipeSecurityAttributes::~PipeSecurityAttributes() {
    if (everyoneSID_ != nullptr)
        FreeSid(everyoneSID_);
    if (allAppsSID_ != nullptr)
        FreeSid(allAppsSID_);
    if (securittyDescriptor_ != nullptr)
        LocalFree(securittyDescriptor_);
    if (acl_ != nullptr)
        LocalFree(acl_);
}

} // namespace PIME
