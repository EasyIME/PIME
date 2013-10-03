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

#ifndef IME_IME_MODULE_H
#define IME_IME_MODULE_H

#include <Unknwn.h>
#include <Windows.h>
#include <Ctffunc.h>
#include <list>
#include "WindowsVersion.h"

namespace Ime {

class TextService;
class DisplayAttributeInfo;

class ImeModule:
	public IClassFactory,
	public ITfFnConfigure {
public:
	ImeModule(HMODULE module, const CLSID& textServiceClsid);
	virtual ~ImeModule(void);

	// public methods
	HINSTANCE hInstance() const {
		return hInstance_;
	}

	const CLSID& textServiceClsid() const {
		return textServiceClsid_;
	}

	bool isWindows8Above() {
		return winVer_.isWindows8Above();
	}

	WindowsVersion windowsVersion() const {
		return winVer_;
	}

	// Dll entry points implementations
	HRESULT canUnloadNow();
	HRESULT getClassObject(REFCLSID rclsid, REFIID riid, void **ppvObj);
	HRESULT registerServer(wchar_t* name, const GUID& profileGuid, LANGID languageId, int iconIndex);
	HRESULT unregisterServer(const GUID& profileGuid);

	// should be override by IME implementors
	virtual TextService* createTextService() = 0;
	void freeTextService(TextService* service);

	// called when config dialog needs to be launched
	virtual bool onConfigure(HWND hwndParent);

	// display attributes for composition string
	std::list<DisplayAttributeInfo*>& displayAttrInfos() {
		return displayAttrInfos_;
	}

	bool registerDisplayAttributeInfos();

	DisplayAttributeInfo* inputAttrib() {
		return inputAttrib_;
	}
	
	/*
	DisplayAttributeInfo* convertedAttrib() {
		return convertedAttrib_;
	}
	*/

	const std::list<TextService*>& textServices() const {
		return textServices_;
	}

	// COM-related stuff

	// IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
    STDMETHODIMP_(ULONG) AddRef(void);
    STDMETHODIMP_(ULONG) Release(void);

protected:
    // IClassFactory
    STDMETHODIMP CreateInstance(IUnknown *pUnkOuter, REFIID riid, void **ppvObj);
    STDMETHODIMP LockServer(BOOL fLock);

	// ITfFunction
	STDMETHODIMP GetDisplayName(BSTR *pbstrName);

	// ITfFnConfigure
	STDMETHODIMP Show(HWND hwndParent, LANGID langid, REFGUID rguidProfile);

private:
	volatile unsigned long refCount_;
	HINSTANCE hInstance_;
	CLSID textServiceClsid_;
	wchar_t* tooltip_;

	// display attributes
	std::list<DisplayAttributeInfo*> displayAttrInfos_; // display attribute info
	DisplayAttributeInfo* inputAttrib_;
	// DisplayAttributeInfo* convertedAttrib_;

	WindowsVersion winVer_;
	std::list<TextService*> textServices_;
};

}

#endif
