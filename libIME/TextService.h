#ifndef IME_TEXT_SERVICE_H
#define IME_TEXT_SERVICE_H

#include "libIME.h"
#include <msctf.h>
#include "EditSession.h"

namespace Ime {

class CandidateWindow;

class TextService:
	// TSF interfaces
	public ITfTextInputProcessor,
	public ITfDisplayAttributeProvider,
	// event sinks
	public ITfThreadMgrEventSink,
	public ITfTextEditSink,
	public ITfKeyEventSink,
	public ITfCompositionSink {
public:

	TextService(void);
	virtual ~TextService(void);

	// public methods
	bool isComposing();
	bool isInsertionAllowed(EditSession* session);
	void startComposition(ITfContext* context);
	void endComposition(ITfContext* context);
	bool compositionRect(EditSession* session, RECT* rect);

	void setCompositionString(EditSession* session, const wchar_t* str, int len);

	// virtual functions that IME implementors may need to override
	virtual void onActivate();
	virtual void onDeactivate();

	virtual void onFocus();

	virtual bool filterKeyDown(long key);
	virtual bool onKeyDown(long key, EditSession* session);
	virtual bool filterKeyUp(long key);
	virtual bool onKeyUp(long key, EditSession* session);

	// COM related stuff
public:
    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void **ppvObj);
	STDMETHODIMP_(ULONG) AddRef(void);
	STDMETHODIMP_(ULONG) Release(void);

    // ITfTextInputProcessor
    STDMETHODIMP Activate(ITfThreadMgr *pThreadMgr, TfClientId tfClientId);
    STDMETHODIMP Deactivate();

    // ITfThreadMgrEventSink
    STDMETHODIMP OnInitDocumentMgr(ITfDocumentMgr *pDocMgr);
    STDMETHODIMP OnUninitDocumentMgr(ITfDocumentMgr *pDocMgr);
    STDMETHODIMP OnSetFocus(ITfDocumentMgr *pDocMgrFocus, ITfDocumentMgr *pDocMgrPrevFocus);
    STDMETHODIMP OnPushContext(ITfContext *pContext);
    STDMETHODIMP OnPopContext(ITfContext *pContext);

    // ITfTextEditSink
    STDMETHODIMP OnEndEdit(ITfContext *pContext, TfEditCookie ecReadOnly, ITfEditRecord *pEditRecord);

    // ITfKeyEventSink
    STDMETHODIMP OnSetFocus(BOOL fForeground);
    STDMETHODIMP OnTestKeyDown(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pfEaten);
    STDMETHODIMP OnKeyDown(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pfEaten);
    STDMETHODIMP OnTestKeyUp(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pfEaten);
    STDMETHODIMP OnKeyUp(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pfEaten);
    STDMETHODIMP OnPreservedKey(ITfContext *pContext, REFGUID rguid, BOOL *pfEaten);

    // ITfCompositionSink
    STDMETHODIMP OnCompositionTerminated(TfEditCookie ecWrite, ITfComposition *pComposition);

    // ITfDisplayAttributeProvider
    STDMETHODIMP EnumDisplayAttributeInfo(IEnumTfDisplayAttributeInfo **ppEnum);
    STDMETHODIMP GetDisplayAttributeInfo(REFGUID guidInfo, ITfDisplayAttributeInfo **ppInfo);

protected:
	// edit session classes, used with TSF
	class KeyEditSession: public EditSession {
	public:
		KeyEditSession(TextService* service, ITfContext* context, bool isDown, WPARAM wParam, LPARAM lParam):
			EditSession(service, context),
			isDown_(isDown),
			result_(false),
			wParam_(wParam),
			lParam_(lParam) {
		}
		STDMETHODIMP DoEditSession(TfEditCookie ec);

		WPARAM wParam_;
		LPARAM lParam_;
		bool isDown_;
		bool result_;
	};

	class StartCompositionEditSession: public EditSession {
	public:
		StartCompositionEditSession(TextService* service, ITfContext* context):
			EditSession(service, context){
		}
		STDMETHODIMP DoEditSession(TfEditCookie ec);
	};

	class EndCompositionEditSession: public EditSession {
	public:
		EndCompositionEditSession(TextService* service, ITfContext* context):
			EditSession(service, context){
		}
		STDMETHODIMP DoEditSession(TfEditCookie ec);
	};

	HRESULT doKeyEditSession(TfEditCookie cookie, KeyEditSession* session);
	HRESULT doStartCompositionEditSession(TfEditCookie cookie, StartCompositionEditSession* session);
	HRESULT doEndCompositionEditSession(TfEditCookie cookie, EndCompositionEditSession* session);

	ITfContext* currentContext();

private:
	ITfThreadMgr *threadMgr_;
	TfClientId clientId_;

	// event sink cookies
	DWORD threadMgrEventSinkCookie_;
	DWORD textEditSinkCookie_;
	DWORD compositionSinkCookie_;

	ITfComposition* composition_; // acquired when starting composition, released when ending composition

	CandidateWindow* candidateWindow_;
	long refCount_; // reference counting
};

}

#endif
