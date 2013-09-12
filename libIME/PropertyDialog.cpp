#include "PropertyDialog.h"
#include "PropertyPage.h"
#include <assert.h>
#include <algorithm>

using namespace Ime;
using namespace std;

typedef INT_PTR (WINAPI *PropertySheetFunc)(LPCPROPSHEETHEADER lppsph);
static PropertySheetFunc g_PropertySheetW = NULL;

PropertyDialog::PropertyDialog(void) {
}

PropertyDialog::~PropertyDialog(void) {
	if(!pages_.empty()) {
		for(vector<PropertyPage*>::iterator it = pages_.begin(); it != pages_.end(); ++it) {
			PropertyPage* page = *it;
			delete page;
		}
	}
}

INT_PTR PropertyDialog::showModal(HINSTANCE hInstance, LPCTSTR captionId, LPCTSTR iconId, HWND parent, DWORD flags) {
	assert(pages_.size() > 0);

	// Windows 8 does not allow linking to comctl32.dll
	// when running in app containers.
	// We use LoadLibrary here, but this should only be used in desktop app mode.
	if(!g_PropertySheetW) {
		HMODULE mod = ::LoadLibraryW(L"comctl32.dll");
		g_PropertySheetW = (PropertySheetFunc)::GetProcAddress(mod, "PropertySheetW");
	}

	PROPSHEETPAGE* pages = new PROPSHEETPAGE[pages_.size()];
	for(int i = 0; i < pages_.size(); ++i) {
		pages_[i]->setup(pages[i]);
		pages[i].hInstance = hInstance;
	}

	PROPSHEETHEADER psh = {0};
	psh.dwFlags = flags;
	psh.dwSize = sizeof(PROPSHEETHEADER);
	psh.hInstance = hInstance;
	psh.hwndParent = parent;
	psh.pszIcon = (LPCTSTR)iconId;
	psh.nPages = pages_.size();
	psh.ppsp = pages;
	psh.pszCaption = (LPCTSTR)captionId;

	assert(g_PropertySheetW);
	INT_PTR result = g_PropertySheetW(&psh);
	delete []pages;

	return result;
}

void PropertyDialog::addPage(PropertyPage* page) {
	pages_.push_back(page);
}

void PropertyDialog::removePage(PropertyPage* page) {
	vector<PropertyPage*>::iterator it = std::find(pages_.begin(), pages_.end(), page);
	if(it != pages_.end())
		pages_.erase(it);
}
