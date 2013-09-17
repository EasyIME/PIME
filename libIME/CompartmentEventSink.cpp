#include "CompartmentEventSink.h"
#include <assert.h>

namespace Ime {

CompartmentEventSink::CompartmentEventSink(void):
	refCount_(1) {
}

CompartmentEventSink::~CompartmentEventSink(void) {
}

// COM stuff
// IUnknown
STDMETHODIMP CompartmentEventSink::QueryInterface(REFIID riid, void **ppvObj) {
    if (ppvObj == NULL)
        return E_INVALIDARG;

	if(IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_ITfCompartmentEventSink))
		*ppvObj = (ITfCompartmentEventSink*)this;
	else
		*ppvObj = NULL;

	if(*ppvObj) {
		AddRef();
		return S_OK;
	}
	return E_NOINTERFACE;
}

STDMETHODIMP_(ULONG) CompartmentEventSink::AddRef(void) {
	return ++refCount_;
}

STDMETHODIMP_(ULONG) CompartmentEventSink::Release(void) {
	assert(refCount_ > 0);
	--refCount_;
	if(0 == refCount_)
		delete this;
	return refCount_;
}

// ITfCompartmentEventSink
STDMETHODIMP CompartmentEventSink::OnChange(REFGUID rguid) {
	return S_OK;
}

} // namespace Ime
