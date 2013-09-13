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

#ifndef IME_DISPLAY_ATTRIBUTE_INFO_ENUM_H
#define IME_DISPLAY_ATTRIBUTE_INFO_ENUM_H

#include <msctf.h>
#include <list>
#include "DisplayAttributeInfo.h"
#include "ComPtr.h"

namespace Ime {

class DisplayAttributeProvider;

class DisplayAttributeInfoEnum : public IEnumTfDisplayAttributeInfo {
public:
	DisplayAttributeInfoEnum(DisplayAttributeProvider* provider);
	DisplayAttributeInfoEnum(const DisplayAttributeInfoEnum& other);
	virtual ~DisplayAttributeInfoEnum(void);

    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
    STDMETHODIMP_(ULONG) AddRef(void);
    STDMETHODIMP_(ULONG) Release(void);

    // IEnumTfDisplayAttributeInfo
    STDMETHODIMP Clone(IEnumTfDisplayAttributeInfo **ppEnum);
    STDMETHODIMP Next(ULONG ulCount, ITfDisplayAttributeInfo **rgInfo, ULONG *pcFetched);
    STDMETHODIMP Reset();
    STDMETHODIMP Skip(ULONG ulCount);

private:
	int refCount_;
	std::list<DisplayAttributeInfo*>::iterator iterator_;
	ComPtr<DisplayAttributeProvider> provider_;
};

}

#endif
