#include "ChewingImeModule.h"
#include "ChewingTextService.h"

using namespace Chewing;

// CLSID of our Text service
// {13F2EF08-575C-4D8C-88E0-F67BB8052B84}
const CLSID g_textServiceClsid = {
	0x13f2ef08, 0x575c, 0x4d8c, { 0x88, 0xe0, 0xf6, 0x7b, 0xb8, 0x5, 0x2b, 0x84 }
};

ImeModule::ImeModule(HMODULE module):
	Ime::ImeModule(module, g_textServiceClsid),
	config_() {
	// load configurations
	config_.load();
}

ImeModule::~ImeModule(void) {
}

// virtual
Ime::TextService* ImeModule::createTextService() {
	TextService* service = new Chewing::TextService(this);
	return service;
}
