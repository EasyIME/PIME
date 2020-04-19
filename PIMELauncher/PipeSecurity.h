#pragma once

#include <Windows.h>
#include <AccCtrl.h>

#include <memory>

namespace PIME {


class PipeSecurityAttributes {
public:

    PipeSecurityAttributes();

    ~PipeSecurityAttributes();

    SECURITY_ATTRIBUTES* get() {
        return &securityAttributes_;
    }

private:
    // security attribute stuff for creating the server pipe
    PSECURITY_DESCRIPTOR securittyDescriptor_;
    SECURITY_ATTRIBUTES securityAttributes_;
};

} // namespace PIME
