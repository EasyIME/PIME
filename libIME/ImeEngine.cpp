#include "ImeEngine.h"
#include "EditSession.h"
#include "CandidateWindow.h"
#include "LangBarButton.h"
#include "DisplayAttributeInfoEnum.h"
#include "ImeModule.h"

#include <assert.h>
#include <string>
#include <algorithm>

using namespace std;

namespace Ime {

ImeEngine::ImeEngine(ImeModule* module):
	module_(module),
	threadMgr_(NULL),
	clientId_(TF_CLIENTID_NULL),
	activateFlags_(0),
	isKeyboardOpened_(false),
	threadMgrEventSinkCookie_(TF_INVALID_COOKIE),
	textEditSinkCookie_(TF_INVALID_COOKIE),
	compositionSinkCookie_(TF_INVALID_COOKIE),
	keyboardOpenEventSinkCookie_(TF_INVALID_COOKIE),
	globalCompartmentEventSinkCookie_(TF_INVALID_COOKIE),
	langBarSinkCookie_(TF_INVALID_COOKIE),
	composition_(NULL),
	candidateWindow_(NULL) {

	addCompartmentMonitor(GUID_COMPARTMENT_KEYBOARD_OPENCLOSE, false);
}

ImeEngine::~ImeEngine() {
	if(candidateWindow_)
		delete candidateWindow_;

	// This should only happen in rare cases
	if(!compartmentMonitors_.empty()) {
		vector<CompartmentMonitor>::iterator it;
		for(it = compartmentMonitors_.begin(); it != compartmentMonitors_.end(); ++it) {
			ComQIPtr<ITfSource> source;
			if(it->isGlobal)
				source = globalCompartment(it->guid);
			else
				source = threadCompartment(it->guid);
			source->UnadviseSink(it->cookie);
		}
	}

	if(!langBarButtons_.empty()) {
		for(vector<LangBarButton*>::iterator it = langBarButtons_.begin(); it != langBarButtons_.end(); ++it) {
			LangBarButton* button = *it;
			button->Release();
		}
	}
	if(langBarMgr_) {
		langBarMgr_->UnadviseEventSink(langBarSinkCookie_);
	}
	langBarMgr_ = NULL;
}


// public methods

ImeModule* ImeEngine::imeModule() const {
	return module_;
}

ITfThreadMgr* ImeEngine::threadMgr() const {
	return threadMgr_;
}

TfClientId ImeEngine::clientId() const {
	return clientId_;
}


// language bar
DWORD ImeEngine::langBarStatus() const {
	if(langBarMgr_) {
		DWORD status;
		if(langBarMgr_->GetShowFloatingStatus(&status) == S_OK) {
			return status;
		}
	}
	return 0;
}

void ImeEngine::addButton(LangBarButton* button) {
	if(button) {
		langBarButtons_.push_back(button);
		button->AddRef();
		if(isActivated()) {
			ITfLangBarItemMgr* langBarItemMgr;
			if(threadMgr_->QueryInterface(IID_ITfLangBarItemMgr, (void**)&langBarItemMgr) == S_OK) {
				langBarItemMgr->AddItem(button);
				langBarItemMgr->Release();
			}
		}
	}
}

void ImeEngine::removeButton(LangBarButton* button) {
	if(button) {
		vector<LangBarButton*>::iterator it;
		it = find(langBarButtons_.begin(), langBarButtons_.end(), button);
		if(it != langBarButtons_.end()) {
			if(isActivated()) {
				ITfLangBarItemMgr* langBarItemMgr;
				if(threadMgr_->QueryInterface(IID_ITfLangBarItemMgr, (void**)&langBarItemMgr) == S_OK) {
					langBarItemMgr->RemoveItem(button);
					langBarItemMgr->Release();
				}
			}
			button->Release();
			langBarButtons_.erase(it);
		}
	}
}

// preserved key
void ImeEngine::addPreservedKey(UINT keyCode, UINT modifiers, const GUID& guid) {
	PreservedKey preservedKey;
	preservedKey.guid = guid;
	preservedKey.uVKey = keyCode;
	preservedKey.uModifiers = modifiers;
	preservedKeys_.push_back(preservedKey);
	if(threadMgr_) { // our text service is activated
		ITfKeystrokeMgr *keystrokeMgr;
		if (threadMgr_->QueryInterface(IID_ITfKeystrokeMgr, (void **)&keystrokeMgr) == S_OK) {
			keystrokeMgr->PreserveKey(clientId_, guid, &preservedKey, NULL, 0);
			keystrokeMgr->Release();
		}
	}
}

void ImeEngine::removePreservedKey(const GUID& guid) {
	vector<PreservedKey>::iterator it;
	for(it = preservedKeys_.begin(); it != preservedKeys_.end(); ++it) {
		PreservedKey& preservedKey = *it;
		if(::IsEqualIID(preservedKey.guid, guid)) {
			if(threadMgr_) { // our text service is activated
				ITfKeystrokeMgr *keystrokeMgr;
				if (threadMgr_->QueryInterface(IID_ITfKeystrokeMgr, (void **)&keystrokeMgr) == S_OK) {
					keystrokeMgr->UnpreserveKey(preservedKey.guid, &preservedKey);
					keystrokeMgr->Release();
				}
			}
			preservedKeys_.erase(it);
			break;
		}
	}
}


// text composition

bool ImeEngine::isComposing() {
	return (composition_ != NULL);
}

// is keyboard disabled for the context (NULL means current context)
bool ImeEngine::isKeyboardDisabled(ITfContext* context) {
	return (contextCompartmentValue(GUID_COMPARTMENT_KEYBOARD_DISABLED, context)
		|| contextCompartmentValue(GUID_COMPARTMENT_EMPTYCONTEXT, context));
}

// is keyboard opened for the whole thread
bool ImeEngine::isKeyboardOpened() {
	return isKeyboardOpened_;
}

void ImeEngine::setKeyboardOpen(bool open) {
	if(open != isKeyboardOpened_) {
		setThreadCompartmentValue(GUID_COMPARTMENT_KEYBOARD_OPENCLOSE, (DWORD)open);
	}
}


// check if current insertion point is in the range of composition.
// if not in range, insertion is now allowed
bool ImeEngine::isInsertionAllowed(EditSession* session) {
	TfEditCookie cookie = session->editCookie();
	TF_SELECTION selection;
	ULONG selectionNum;
	if(isComposing()) {
		if(session->context()->GetSelection(cookie, TF_DEFAULT_SELECTION, 1, &selection, &selectionNum) == S_OK) {
			ITfRange* compositionRange;
			if(composition_->GetRange(&compositionRange) == S_OK) {
				bool allowed = false;
				// check if current selection is covered by composition range
				LONG compareResult1;
				LONG compareResult2;
				if(selection.range->CompareStart(cookie, compositionRange, TF_ANCHOR_START, &compareResult1) == S_OK
					&& selection.range->CompareStart(cookie, compositionRange, TF_ANCHOR_END, &compareResult2) == S_OK) {
					if(compareResult1 == -1 && compareResult2 == +1)
						allowed = true;
				}
				compositionRange->Release();
			}
			if(selection.range)
				selection.range->Release();
		}
	}
	return false;
}

void ImeEngine::startComposition(ITfContext* context) {
	assert(context);
	HRESULT sessionResult;
	StartCompositionEditSession* session = new StartCompositionEditSession(this, context);
	context->RequestEditSession(clientId_, session, TF_ES_SYNC|TF_ES_READWRITE, &sessionResult);
	session->Release();
}

void ImeEngine::endComposition(ITfContext* context) {
	assert(context);
	HRESULT sessionResult;
	EndCompositionEditSession* session = new EndCompositionEditSession(this, context);
	context->RequestEditSession(clientId_, session, TF_ES_SYNC|TF_ES_READWRITE, &sessionResult);
	session->Release();
}

void ImeEngine::setCompositionString(EditSession* session, const wchar_t* str, int len) {
	ITfContext* context = session->context();
	if(context) {
		TfEditCookie editCookie = session->editCookie();
		TF_SELECTION selection;
		ULONG selectionNum;
		// get current selection/insertion point
		if(context->GetSelection(editCookie, TF_DEFAULT_SELECTION, 1, &selection, &selectionNum) == S_OK) {
			ComPtr<ITfRange> compositionRange;
			if(composition_->GetRange(&compositionRange) == S_OK) {
				bool selPosInComposition = true;
				// if current insertion point is not covered by composition, we cannot insert text here.
				if(selPosInComposition) {
					// replace context of composion area with the new string.
					compositionRange->SetText(editCookie, TF_ST_CORRECTION, str, len);

					// move the insertion point to end of the composition string
					selection.range->Collapse(editCookie, TF_ANCHOR_END);
					context->SetSelection(editCookie, 1, &selection);
				}

				// set display attribute to the composition range
				ComPtr<ITfProperty> dispAttrProp;
				if(context->GetProperty(GUID_PROP_ATTRIBUTE, &dispAttrProp) == S_OK) {
					VARIANT val;
					val.vt = VT_I4;
					val.lVal = module_->inputAttrib()->atom();
					dispAttrProp->SetValue(editCookie, compositionRange, &val);
				}
			}
			selection.range->Release();
		}
	}
}

// set cursor position in the composition area
// 0 means the start pos of composition string
void ImeEngine::setCompositionCursor(EditSession* session, int pos) {
	TF_SELECTION selection;
	ULONG selectionNum;
	// get current selection
	if(session->context()->GetSelection(session->editCookie(), TF_DEFAULT_SELECTION, 1, &selection, &selectionNum) == S_OK) {
		// get composition range
		ITfRange* compositionRange;
		if(composition_->GetRange(&compositionRange) == S_OK) {
			// make the start of selectionRange the same as that of compositionRange
			selection.range->ShiftStartToRange(session->editCookie(), compositionRange, TF_ANCHOR_START);
			selection.range->Collapse(session->editCookie(), TF_ANCHOR_START);
			LONG moved;
			// move the start anchor to right
			selection.range->ShiftStart(session->editCookie(), (LONG)pos, &moved, NULL);
			selection.range->Collapse(session->editCookie(), TF_ANCHOR_START);
			// set the new selection to the context
			session->context()->SetSelection(session->editCookie(), 1, &selection);
			compositionRange->Release();
		}
		selection.range->Release();
	}
}

// compartment handling
ComPtr<ITfCompartment> ImeEngine::globalCompartment(const GUID& key) {
	if(threadMgr_) {
		ComQIPtr<ITfCompartmentMgr> compartmentMgr;
		if(threadMgr_->GetGlobalCompartment(&compartmentMgr) == S_OK) {
			ComPtr<ITfCompartment> compartment;
			compartmentMgr->GetCompartment(key, &compartment);
			return compartment;
		}
	}
	return NULL;
}

ComPtr<ITfCompartment> ImeEngine::threadCompartment(const GUID& key) {
	if(threadMgr_) {
		ComQIPtr<ITfCompartmentMgr> compartmentMgr = threadMgr_;
		if(compartmentMgr) {
			ComPtr<ITfCompartment> compartment;
			compartmentMgr->GetCompartment(key, &compartment);
			return compartment;
		}
	}
	return NULL;
}

ComPtr<ITfCompartment> ImeEngine::contextCompartment(const GUID& key, ITfContext* context) {
	ITfContext* curContext = NULL;
	if(!context) {
		curContext = currentContext();
		context = curContext;
	}
	if(context) {
		ComQIPtr<ITfCompartmentMgr> compartmentMgr = context;
		if(compartmentMgr) {
			ComPtr<ITfCompartment> compartment;
			compartmentMgr->GetCompartment(key, &compartment);
			return compartment;
		}
	}
	if(curContext)
		curContext->Release();
	return NULL;
}


DWORD ImeEngine::globalCompartmentValue(const GUID& key) {
	ComPtr<ITfCompartment> compartment = globalCompartment(key);
	if(compartment) {
		VARIANT var;
		if(compartment->GetValue(&var) == S_OK && var.vt == VT_I4) {
			return (DWORD)var.lVal;
		}
	}
	return 0;
}

DWORD ImeEngine::threadCompartmentValue(const GUID& key) {
	ComPtr<ITfCompartment> compartment = threadCompartment(key);
	if(compartment) {
		VARIANT var;
		::VariantInit(&var);
		HRESULT r = compartment->GetValue(&var);
		if(r == S_OK) {
			if(var.vt == VT_I4)
				return (DWORD)var.lVal;
		}
	}
	return 0;
}

DWORD ImeEngine::contextCompartmentValue(const GUID& key, ITfContext* context) {
	ComPtr<ITfCompartment> compartment = contextCompartment(key, context);
	if(compartment) {
		VARIANT var;
		if(compartment->GetValue(&var) == S_OK && var.vt == VT_I4) {
			return (DWORD)var.lVal;
		}
	}
	return 0;
}

void ImeEngine::setGlobalCompartmentValue(const GUID& key, DWORD value) {
	if(threadMgr_) {
		ComPtr<ITfCompartment> compartment = globalCompartment(key);
		if(compartment) {
			VARIANT var;
			::VariantInit(&var);
			var.vt = VT_I4;
			var.lVal = value;
			compartment->SetValue(clientId_, &var);
		}
	}
	else {
		// if we don't have a thread manager (this is possible when we try to set
		// a global compartment value while the text service is not activated)
		ComPtr<ITfThreadMgr> threadMgr;
		if(::CoCreateInstance(CLSID_TF_ThreadMgr, NULL, CLSCTX_INPROC_SERVER, IID_ITfThreadMgr, (void**)&threadMgr) == S_OK) {
			if(threadMgr) {
				ComPtr<ITfCompartmentMgr> compartmentMgr;
				if(threadMgr->GetGlobalCompartment(&compartmentMgr) == S_OK) {
					ComPtr<ITfCompartment> compartment;
					if(compartmentMgr->GetCompartment(key, &compartment) == S_OK && compartment) {
						TfClientId id;
						if(threadMgr->Activate(&id) == S_OK) {
							VARIANT var;
							::VariantInit(&var);
							var.vt = VT_I4;
							var.lVal = value;
							compartment->SetValue(id, &var);
							threadMgr->Deactivate();
						}
					}
				}
			}
		}
	}
}

void ImeEngine::setThreadCompartmentValue(const GUID& key, DWORD value) {
	ComPtr<ITfCompartment> compartment = threadCompartment(key);
	if(compartment) {
		VARIANT var;
		::VariantInit(&var);
		var.vt = VT_I4;
		var.lVal = value;
		compartment->SetValue(clientId_, &var);
	}
}

void ImeEngine::setContextCompartmentValue(const GUID& key, DWORD value, ITfContext* context) {
	ComPtr<ITfCompartment> compartment = contextCompartment(key, context);
	if(compartment) {
		VARIANT var;
		::VariantInit(&var);
		var.vt = VT_I4;
		var.lVal = value;
		compartment->SetValue(clientId_, &var);
	}
}


void ImeEngine::addCompartmentMonitor(const GUID key, bool isGlobal) {
	CompartmentMonitor monitor;
	monitor.guid = key;
	monitor.cookie = 0;
	monitor.isGlobal = isGlobal;
	// if the text service is activated
	if(threadMgr_) {
		ComQIPtr<ITfSource> source;
		if(isGlobal)
			source = globalCompartment(key);
		else
			source = threadCompartment(key);
		if(source) {
			source->AdviseSink(IID_ITfCompartmentEventSink, (ITfCompartmentEventSink*)this, &monitor.cookie);
		}
	}
	compartmentMonitors_.push_back(monitor);
}

void ImeEngine::removeCompartmentMonitor(const GUID key) {
	vector<CompartmentMonitor>::iterator it;
	it = find(compartmentMonitors_.begin(), compartmentMonitors_.end(), key);
	if(it != compartmentMonitors_.end()) {
		if(threadMgr_) {
			ComQIPtr<ITfSource> source;
			if(it->isGlobal)
				source = globalCompartment(key);
			else
				source = threadCompartment(key);
			source->UnadviseSink(it->cookie);
		}
		compartmentMonitors_.erase(it);
	}
}


// virtual
void ImeEngine::onActivate() {
}

// virtual
void ImeEngine::onDeactivate() {
}

// virtual
bool ImeEngine::filterKeyDown(KeyEvent& keyEvent) {
	return false;
}

// virtual
bool ImeEngine::onKeyDown(KeyEvent& keyEvent, EditSession* session) {
	return false;
}

// virtual
bool ImeEngine::filterKeyUp(KeyEvent& keyEvent) {
	return false;
}

// virtual
bool ImeEngine::onKeyUp(KeyEvent& keyEvent, EditSession* session) {
	return false;
}

// virtual
bool ImeEngine::onPreservedKey(const GUID& guid) {
	return false;
}

// virtual
void ImeEngine::onSetFocus() {
}

// virtual
void ImeEngine::onKillFocus() {
}

bool ImeEngine::onCommand(UINT id, CommandType type) {
	return false;
}

// virtual
void ImeEngine::onCompartmentChanged(const GUID& key) {
	// keyboard status changed, this is threadMgr specific
	// See explanations on TSF aware blog:
	// http://blogs.msdn.com/b/tsfaware/archive/2007/05/30/what-is-a-keyboard.aspx
	if(::IsEqualGUID(key, GUID_COMPARTMENT_KEYBOARD_OPENCLOSE)) {
		isKeyboardOpened_ = threadCompartmentValue(key) ? true : false;
		onKeyboardStatusChanged(isKeyboardOpened_);
	}
}

// virtual
void ImeEngine::onLangBarStatusChanged(int newStatus) {
}

// called when the keyboard is opened or closed
// virtual
void ImeEngine::onKeyboardStatusChanged(bool opened) {
}

// called just before current composition is terminated for doing cleanup.
// if forced is true, the composition is terminated by others, such as
// the input focus is grabbed by another application.
// if forced is false, the composition is terminated gracefully by endComposition().
// virtual
void ImeEngine::onCompositionTerminated(bool forced) {
}

}
