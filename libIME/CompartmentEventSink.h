#ifndef IME_COMPARTMENT_EVENT_SINK_H
#define IME_COMPARTMENT_EVENT_SINK_H

#include <msctf.h>

namespace Ime {

// base class used to implement specific compartment sink
// currently the class is not used in libIME

class CompartmentEventSink : public ITfCompartmentEventSink {
public:
	CompartmentEventSink(void);
	virtual ~CompartmentEventSink(void);

	// COM stuff
    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
	STDMETHODIMP_(ULONG) AddRef(void);
	STDMETHODIMP_(ULONG) Release(void);

	// ITfCompartmentEventSink
	STDMETHODIMP OnChange(REFGUID rguid);

private:
	int refCount_;
};

}

#endif
