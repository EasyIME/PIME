#ifndef CHEWING_TEXT_SERVICE_H
#define CHEWING_TEXT_SERVICE_H

#include <LibIME/TextService.h>

namespace Chewing {

class TextService: public Ime::TextService {
public:
	TextService(void);
	virtual ~TextService(void);

	virtual bool onKeyDown(long key);
};

}

#endif
