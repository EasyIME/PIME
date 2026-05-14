//go:build windows

package rime

import (
	"log"
	"sync"

	"github.com/EasyIME/pime-go/pime"
)

type nativeBackend struct {
	sessionID RimeSessionId
}

var (
	rimeInitOnce sync.Once
	rimeInitOK   bool
)

func newNativeBackend() rimeBackend {
	return &nativeBackend{}
}

func (b *nativeBackend) Initialize(sharedDir, userDir string, firstRun bool) bool {
	rimeInitOnce.Do(func() {
		rimeInitOK = RimeInit(sharedDir, userDir, APP, APP_VERSION, firstRun)
		if !rimeInitOK {
			log.Println("RIME 初始化失败，原生后端不可用")
		}
	})
	return rimeInitOK
}

func (b *nativeBackend) EnsureSession() bool {
	if b.sessionID != 0 && FindSession(b.sessionID) {
		return true
	}
	sessionID, ok := StartSession()
	if ok {
		b.sessionID = sessionID
	}
	return ok
}

func (b *nativeBackend) DestroySession() {
	if b.sessionID != 0 {
		EndSession(b.sessionID)
		b.sessionID = 0
	}
}

func (b *nativeBackend) ClearComposition() {
	if b.sessionID != 0 {
		ClearComposition(b.sessionID)
	}
}

func (b *nativeBackend) ProcessKey(req *pime.Request, translatedKeyCode, modifiers int) bool {
	if !b.EnsureSession() {
		return false
	}
	return ProcessKey(b.sessionID, translatedKeyCode, modifiers)
}

func (b *nativeBackend) State() rimeState {
	state := rimeState{}
	if b.sessionID == 0 {
		return state
	}
	if commit, ok := GetCommit(b.sessionID); ok {
		state.CommitString = commit.Text
	}
	if composition, ok := GetComposition(b.sessionID); ok {
		state.Composition = composition.Preedit
		state.CursorPos = composition.CursorPos
		state.SelStart = composition.SelStart
		state.SelEnd = composition.SelEnd
	}
	if menu, ok := GetMenu(b.sessionID); ok {
		candidates := make([]candidateItem, 0, len(menu.Candidates))
		for _, candidate := range menu.Candidates {
			candidates = append(candidates, candidateItem{
				Text:    candidate.Text,
				Comment: candidate.Comment,
			})
		}
		state.Candidates = candidates
		state.CandidateCursor = menu.HighlightedCandidateIndex
		state.SelectKeys = menu.SelectKeys
	}
	state.AsciiMode = b.GetOption("ascii_mode")
	state.FullShape = b.GetOption("full_shape")
	return state
}

func (b *nativeBackend) SetOption(name string, value bool) {
	if b.EnsureSession() {
		SetOption(b.sessionID, name, value)
	}
}

func (b *nativeBackend) GetOption(name string) bool {
	if !b.EnsureSession() {
		return false
	}
	return GetOption(b.sessionID, name)
}
