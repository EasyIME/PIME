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

#ifndef IME_DISPLAY_ATTRIBUTE_H
#define IME_DISPLAY_ATTRIBUTE_H

#include <msctf.h>

namespace Ime {

class DisplayAttributeInfo : public ITfDisplayAttributeInfo {
public:
	DisplayAttributeInfo(const GUID& guid);
	virtual ~DisplayAttributeInfo(void);

	// public methods

	void setAtom(TfGuidAtom atom) {
		atom_ = atom;
	}

	TfGuidAtom atom() const {
		return atom_;
	}

	void setTextColor(COLORREF color) {
		attrib_.crText.type = TF_CT_COLORREF;
		attrib_.crText.cr = color;
	}

	void setTextColor(int index) {
		attrib_.crText.type = TF_CT_SYSCOLOR;
		attrib_.crText.nIndex = index;
	}

	void setBackgroundColor(COLORREF color) {
		attrib_.crBk.type = TF_CT_COLORREF;
		attrib_.crBk.cr = color;
	}

	void setBackgroundColor(int index) {
		attrib_.crBk.type = TF_CT_SYSCOLOR;
		attrib_.crBk.nIndex = index;
	}

	void setLineColor(COLORREF color) {
		attrib_.crLine.type = TF_CT_COLORREF;
		attrib_.crLine.cr = color;
	}

	void setLineColor(int index) {
		attrib_.crLine.type = TF_CT_SYSCOLOR;
		attrib_.crLine.nIndex = index;
	}

	void setLineStyle(TF_DA_LINESTYLE style) {
		attrib_.lsStyle = style;
	}

	void setLineBold(bool bold) {
		attrib_.fBoldLine = (BOOL)bold;
	}

	void setAttrInfo(TF_DA_ATTR_INFO attr) {
		attrib_.bAttr = attr;
	}

	void setDescription(wchar_t* desc) {
		if(desc_)
			free(desc_);
		desc_ = _wcsdup(desc);
	}

	const GUID& guid() const {
		return guid_;
	}

    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
    STDMETHODIMP_(ULONG) AddRef(void);
    STDMETHODIMP_(ULONG) Release(void);

    // ITfDisplayAttributeInfo
    STDMETHODIMP GetGUID(GUID *pguid);
    STDMETHODIMP GetDescription(BSTR *pbstrDesc);
    STDMETHODIMP GetAttributeInfo(TF_DISPLAYATTRIBUTE *ptfDisplayAttr);
    STDMETHODIMP SetAttributeInfo(const TF_DISPLAYATTRIBUTE *ptfDisplayAttr);
    STDMETHODIMP Reset();

private:
	int refCount_;
	TfGuidAtom atom_;
	GUID guid_;
	wchar_t* desc_;
	TF_DISPLAYATTRIBUTE attrib_;
};

}

#endif
