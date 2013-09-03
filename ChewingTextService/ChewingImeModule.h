#ifndef CHEWING_IME_MODULE_H
#define CHEWING_IME_MODULE_H

#include <LibIME/ImeModule.h>

namespace Chewing {

class ImeModule : public Ime::ImeModule {
public:
	ImeModule(HMODULE module);
	virtual ~ImeModule(void);

	virtual Ime::TextService* createTextService();
};

}

#endif
