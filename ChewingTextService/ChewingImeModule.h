#ifndef CHEWING_IME_MODULE_H
#define CHEWING_IME_MODULE_H

#include <LibIME/ImeModule.h>
#include "ChewingConfig.h"

namespace Chewing {

class ImeModule : public Ime::ImeModule {
public:
	ImeModule(HMODULE module);
	virtual ~ImeModule(void);

	virtual Ime::TextService* createTextService();

	Config& config() {
		return config_;
	}

private:
	Config config_;
};

}

#endif
