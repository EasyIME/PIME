#ifndef IME_IME_ENGINE_H
#define IME_IME_ENGINE_H

#include "libIME.h"
#include <msctf.h>
#include "EditSession.h"
#include "KeyEvent.h"
#include "ComPtr.h"

#include <vector>
#include <list>

// for Windows 8 support
#ifndef TF_TMF_IMMERSIVEMODE // this is defined in Win 8 SDK
#define TF_TMF_IMMERSIVEMODE	0x40000000
#endif

namespace Ime {

class ImeModule;
class CandidateWindow;
class LangBarButton;

class ImeEngine {
public:
	enum CommandType { // used in onCommand()
		COMMAND_LEFT_CLICK,
		COMMAND_RIGHT_CLICK,
		COMMAND_MENU
	};

	ImeEngine(ImeModule* module);
	virtual ~ImeEngine();

	// public methods
	ImeModule* imeModule() const;

	ITfThreadMgr* threadMgr() const;

	TfClientId clientId() const;

	ITfContext* currentContext();

	bool isActivated() const {
		return (threadMgr() != NULL);
	}

	DWORD activateFlags() const {
		return activateFlags_;
	}

	// running in Windows 8 app mode
	bool isImmersive() const {
		return (activateFlags_ & TF_TMF_IMMERSIVEMODE) != 0;
	}

	DWORD langBarStatus() const;

	// language bar buttons
	void addButton(LangBarButton* button);
	void removeButton(LangBarButton* button);

	// preserved keys
	void addPreservedKey(UINT keyCode, UINT modifiers, const GUID& guid);
	void removePreservedKey(const GUID& guid);

	// text composition handling
	bool isComposing();

	// is keyboard disabled for the context (NULL means current context)
	bool isKeyboardDisabled(ITfContext* context = NULL);
	
	// is keyboard opened for the whole thread
	bool isKeyboardOpened();
	void setKeyboardOpen(bool open);

	bool isInsertionAllowed(EditSession* session);
	void startComposition(ITfContext* context);
	void endComposition(ITfContext* context);
	bool compositionRect(EditSession* session, RECT* rect);
	bool selectionRect(EditSession* session, RECT* rect);
	HWND compositionWindow(EditSession* session);

	void setCompositionString(EditSession* session, const wchar_t* str, int len);
	void setCompositionCursor(EditSession* session, int pos);

	// compartment handling
	ComPtr<ITfCompartment> globalCompartment(const GUID& key);
	ComPtr<ITfCompartment> threadCompartment(const GUID& key);
	ComPtr<ITfCompartment> contextCompartment(const GUID& key, ITfContext* context = NULL);

	DWORD globalCompartmentValue(const GUID& key);
	DWORD threadCompartmentValue(const GUID& key);
	DWORD contextCompartmentValue(const GUID& key, ITfContext* context = NULL);

	void setGlobalCompartmentValue(const GUID& key, DWORD value);
	void setThreadCompartmentValue(const GUID& key, DWORD value);
	void setContextCompartmentValue(const GUID& key, DWORD value, ITfContext* context = NULL);

	// manage sinks to global or thread compartment (context specific compartment is not used)
	void addCompartmentMonitor(const GUID key, bool isGlobal = false);
	void removeCompartmentMonitor(const GUID key);

	// virtual functions that IME implementors may need to override
	virtual void onActivate();
	virtual void onDeactivate();

	virtual void onSetFocus();
	virtual void onKillFocus();

	virtual bool filterKeyDown(KeyEvent& keyEvent);
	virtual bool onKeyDown(KeyEvent& keyEvent, EditSession* session);
	
	virtual bool filterKeyUp(KeyEvent& keyEvent);
	virtual bool onKeyUp(KeyEvent& keyEvent, EditSession* session);

	virtual bool onPreservedKey(const GUID& guid);

	// called when a language button or menu item is clicked
	virtual bool onCommand(UINT id, CommandType type);

	// called when a value in the global or thread compartment changed.
	virtual void onCompartmentChanged(const GUID& key);

	virtual void onLangBarStatusChanged(int newStatus);

	// called when the keyboard is opened or closed
	virtual void onKeyboardStatusChanged(bool opened);

	// called just before current composition is terminated for doing cleanup.
	// if forced is true, the composition is terminated by others, such as
	// the input focus is grabbed by another application.
	// if forced is false, the composition is terminated gracefully by endComposition().
	virtual void onCompositionTerminated(bool forced);

private:
	ComPtr<ImeModule> module_;
	ComPtr<ITfThreadMgr> threadMgr_;
	TfClientId clientId_;
	DWORD activateFlags_;
	bool isKeyboardOpened_;

	// event sink cookies
	DWORD threadMgrEventSinkCookie_;
	DWORD textEditSinkCookie_;
	DWORD compositionSinkCookie_;
	DWORD keyboardOpenEventSinkCookie_;
	DWORD globalCompartmentEventSinkCookie_;
	DWORD langBarSinkCookie_;

	ITfComposition* composition_; // acquired when starting composition, released when ending composition
	CandidateWindow* candidateWindow_;
	ComPtr<ITfLangBarMgr> langBarMgr_;
	std::vector<LangBarButton*> langBarButtons_;
	std::vector<PreservedKey> preservedKeys_;
	std::vector<CompartmentMonitor> compartmentMonitors_;
};

}

#endif
