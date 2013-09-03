#include "ChewingImeModule.h"
#include "ChewingTextService.h"

using namespace Chewing;

ImeModule::ImeModule(HMODULE module):
	Ime::ImeModule(module) {
}

ImeModule::~ImeModule(void) {
}

// virtual
Ime::TextService* ImeModule::createTextService() {
	TextService* service = new Chewing::TextService();
	return service;
}
