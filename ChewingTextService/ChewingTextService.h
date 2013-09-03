#ifndef CHEWING_TEXT_SERVICE_H
#define CHEWING_TEXT_SERVICE_H

#include <LibIME/TextService.h>
#include <chewing.h>

namespace Chewing {

class TextService: public Ime::TextService {
public:
	TextService(void);
	virtual ~TextService(void);

	virtual void onActivate();
	virtual void onDeactivate();

	virtual void onFocus();

	virtual bool onKeyDown(long key);
	virtual bool onKeyUp(long key);

private:
	ChewingContext* chewingContext_;
};

}

#endif
