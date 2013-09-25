//
//	Copyright (C) 2013 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
//
//	This library is free software; you can redistribute it and/or
//	modify it under the terms of the GNU Library General Public
//	License as published by the Free Software Foundation; either
//	version 2 of the License, or (at your option) any later version.
//
//	This library is distributed in the hope that it will be useful,
//	but WITHOUT ANY WARRANTY; without even the implied warranty of
//	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//	Library General Public License for more details.
//
//	You should have received a copy of the GNU Library General Public
//	License along with this library; if not, write to the
//	Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
//	Boston, MA  02110-1301, USA.
//

#include <Windows.h>
#include <libIME/Dialog.h>
#include <libIME/PropertyDialog.h>
#include <libIME/WindowsVersion.h>
#include <libIME/ComPtr.h>
#include "TypingPropertyPage.h"
#include "UiPropertyPage.h"
#include "KeyboardPropertyPage.h"
#include "SymbolsPropertyPage.h"
#include "AboutDialog.h"
#include "resource.h"
#include <CommCtrl.h>
#include <Msctf.h>

namespace Chewing {

// {F4D1E543-FB2C-48D7-B78D-20394F355381} // global compartment GUID for config change notification
static const GUID g_configChangedGuid = 
{ 0xf4d1e543, 0xfb2c, 0x48d7, { 0xb7, 0x8d, 0x20, 0x39, 0x4f, 0x35, 0x53, 0x81 } };

static void initControls() {
	INITCOMMONCONTROLSEX ic;
	ic.dwSize = sizeof(ic);
	ic.dwICC = ICC_UPDOWN_CLASS;
	::InitCommonControlsEx(&ic);

	// Init RichEdit 2.0
	// HMODULE riched20;
	// riched20 = LoadLibraryA("RICHED20.DLL");
}

static void configDialog(HINSTANCE hInstance) {
	initControls();

	Ime::WindowsVersion winVer;
	Config config(winVer);
	config.load();

	Ime::PropertyDialog dlg;
	TypingPropertyPage* typingPage = new TypingPropertyPage(&config);
	UiPropertyPage* uiPage = new UiPropertyPage(&config);
	KeyboardPropertyPage* keyboardPage = new KeyboardPropertyPage(&config);
	SymbolsPropertyPage* symbolsPage = new SymbolsPropertyPage(&config);
	dlg.addPage(typingPage);
	dlg.addPage(uiPage);
	dlg.addPage(keyboardPage);
	dlg.addPage(symbolsPage);
	INT_PTR ret = dlg.showModal(hInstance, (LPCTSTR)IDS_CONFIG_TITLE, 0, HWND_DESKTOP);
	if(ret) { // the user clicks OK button
		// get current time stamp and set the value to global compartment to notify all
		// text service instances to reload their config.
		// TextService::onCompartmentChanged() of all other instances will be triggered.
		config.save();

		DWORD stamp = ::GetTickCount();
		if(stamp == Config::INVALID_TIMESTAMP) // this is almost impossible
			stamp = 0;
		// set global compartment value to notify existing ChewingTextService instances
		::CoInitialize(NULL); // initialize COM
		Ime::ComPtr<ITfThreadMgr> threadMgr;
		if(CoCreateInstance(CLSID_TF_ThreadMgr, NULL, CLSCTX_INPROC_SERVER, IID_ITfThreadMgr, (void**)&threadMgr) == S_OK) {
			TfClientId clientId = 0;
			if(threadMgr->Activate(&clientId) == S_OK) {
				Ime::ComPtr<ITfCompartmentMgr> compartmentMgr;
				if(threadMgr->GetGlobalCompartment(&compartmentMgr) == S_OK) {
					Ime::ComPtr<ITfCompartment> compartment;
					if(compartmentMgr->GetCompartment(g_configChangedGuid, &compartment) == S_OK) {
						VARIANT var;
						VariantInit(&var);
						var.vt = VT_I4;
						var.lVal = ::GetTickCount(); // set current timestamp
						compartment->SetValue(clientId, &var);
					}
				}
				threadMgr->Deactivate();
			}
		}
		::CoUninitialize();
	}
}

static void aboutDialog(HINSTANCE hInstance) {
	AboutDialog dlg;
	dlg.showModal(hInstance, IDD_ABOUT);
}

}

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, PWSTR cmdLine, int nShow) {
	if(cmdLine && wcscmp(cmdLine, L"/about") == 0) // show about
		Chewing::aboutDialog(hInstance);
	else // show configuration dialog
		Chewing::configDialog(hInstance);
	return 0;
}
