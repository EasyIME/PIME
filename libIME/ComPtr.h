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

#ifndef IME_COM_PTR_H
#define IME_COM_PTR_H

// ATL-indepdent smart pointers for COM objects
// very similar to the ones provided by ATL (CComPtr & CComQIPtr).

namespace Ime {

// a smart pointer for COM interface/object
// automatic AddRef() on copy and Release() on destruction.
template <class T>
class ComPtr {
public:
	ComPtr(void): p_(NULL) {
	}

	ComPtr(T* p): p_(p) {
		if(p_)
			p_->AddRef();
	}

	ComPtr(const ComPtr& other): p_(other.p_) {
		if(p_)
			p_->AddRef();
	}

	~ComPtr(void) {
		if(p_) {
			p_->Release();
		}
	}

	T& operator * () const {
		return *p_;
	}

	T** operator & () {
		return &p_;
	}

	T* operator-> () const {
        return p_;
    }

	operator T* () const {
		return p_;
	}

	bool operator !() const {
		return !p_;
	}

	bool operator == (T* p) const {
		return p == p_;
	}

	bool operator != (T* p) const {
		return p != p_;
	}

	bool operator < (T* p) const {
		return p_ < p;
	}

	ComPtr& operator = (T* p) {
		if(p_)
			p_->Release();
		p_ = p;
		if(p_)
			p_->AddRef();
		return *this;
	}

protected:
	T* p_;
};


// a smart pointer for COM interface/object with automatic QueryInterface
// QueryInterface() for interface T was done automatically on
// assignment or construction.
// automatic AddRef() on copy and Release() on destruction.

template <class T>
class ComQIPtr: public ComPtr<T> {

public:
	ComQIPtr(void): ComPtr<T>() {
	}

	ComQIPtr(T* p): ComPtr<T>(p) {
	}

	ComQIPtr(const ComQIPtr& other): ComPtr<T>(other) {
	}

	ComQIPtr(IUnknown* p) {
		if(p) {
			p->QueryInterface(__uuidof(T), (void**)&p_);
		}
	}

	ComQIPtr& operator = (IUnknown* p) {
		ComPtr<T>::operator = (NULL);
		if(p) {
			p->QueryInterface(__uuidof(T), (void**)&p_);
		}
		return *this;
	}

};

}

#endif
