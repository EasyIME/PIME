#ifndef EDIT_SESSION_H
#define EDIT_SESSION_H

#include <msctf.h>

namespace Ime {

class TextService;

class EditSession: public ITfEditSession {
public:
	EditSession(TextService* service, ITfContext* context);
	virtual ~EditSession(void);

	TextService* textService() {
		return textService_;
	}

	ITfContext* context() {
		return context_;
	}

	// COM stuff

    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
	STDMETHODIMP_(ULONG) AddRef(void);
	STDMETHODIMP_(ULONG) Release(void);

    // ITfEditSession
    virtual STDMETHODIMP DoEditSession(TfEditCookie ec) = 0;

protected:
	TextService* textService_;
	ITfContext* context_;

private:
	long refCount_;
};

}

#endif
