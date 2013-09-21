#pragma once
#include <libIME/PropertyPage.h>
#include "ChewingConfig.h"

namespace Chewing {

class KeyboardPropertyPage : public Ime::PropertyPage {
public:
	KeyboardPropertyPage(Config* config);
	virtual ~KeyboardPropertyPage(void);

protected:
	virtual bool onInitDialog();
	virtual void onOK();

private:
	Config* config_;
};

}
