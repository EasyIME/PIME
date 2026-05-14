package rime

import (
	"strings"
	"testing"

	"github.com/EasyIME/pime-go/pime"
)

type testDictEntry struct {
	code  string
	words []candidateItem
}

type testBackend struct {
	session      bool
	composition  string
	candidates   []candidateItem
	commitString string
	asciiMode    bool
	fullShape    bool
}

func newTestBackend() *testBackend {
	return &testBackend{}
}

func (b *testBackend) Initialize(sharedDir, userDir string, firstRun bool) bool {
	return true
}

func (b *testBackend) EnsureSession() bool {
	b.session = true
	return true
}

func (b *testBackend) DestroySession() {
	b.session = false
	b.ClearComposition()
}

func (b *testBackend) ClearComposition() {
	b.composition = ""
	b.candidates = nil
	b.commitString = ""
}

func (b *testBackend) ProcessKey(req *pime.Request, translatedKeyCode, modifiers int) bool {
	b.commitString = ""
	keyCode := req.KeyCode
	charCode := req.CharCode
	if charCode == 0 && keyCode >= 'A' && keyCode <= 'Z' {
		charCode = keyCode + 32
	}
	if b.asciiMode && b.composition == "" && charCode >= 0x20 {
		return false
	}
	if modifiers&releaseMask != 0 {
		return false
	}

	switch keyCode {
	case vkBack:
		if b.composition == "" {
			return false
		}
		b.composition = trimLastRuneForTest(b.composition)
		b.refreshCandidates()
		return true
	case vkEscape:
		if b.composition == "" {
			return false
		}
		b.ClearComposition()
		return true
	case vkReturn, vkSpace:
		if b.composition == "" {
			return false
		}
		b.commitString = b.currentCommit()
		b.composition = ""
		b.candidates = nil
		return true
	}

	if b.composition != "" && keyCode >= '1' && keyCode <= '9' {
		index := keyCode - '1'
		if index >= 0 && index < len(b.candidates) {
			b.commitString = b.candidates[index].Text
			b.composition = ""
			b.candidates = nil
			return true
		}
	}

	if charCode >= 'a' && charCode <= 'z' {
		b.composition += string(rune(charCode))
		b.refreshCandidates()
		return true
	}
	if charCode == '\'' && b.composition != "" && !strings.HasSuffix(b.composition, "'") {
		b.composition += "'"
		b.refreshCandidates()
		return true
	}
	if b.composition != "" && charCode >= 0x20 && charCode != '\'' {
		b.commitString = b.currentCommit() + string(rune(charCode))
		b.composition = ""
		b.candidates = nil
		return true
	}
	return false
}

func (b *testBackend) State() rimeState {
	state := rimeState{
		CommitString:    b.commitString,
		Composition:     b.composition,
		CursorPos:       len(b.composition),
		Candidates:      append([]candidateItem(nil), b.candidates...),
		CandidateCursor: 0,
		SelectKeys:      "1234567890",
		AsciiMode:       b.asciiMode,
		FullShape:       b.fullShape,
	}
	b.commitString = ""
	return state
}

func (b *testBackend) SetOption(name string, value bool) {
	switch name {
	case "ascii_mode":
		b.asciiMode = value
	case "full_shape":
		b.fullShape = value
	}
}

func (b *testBackend) GetOption(name string) bool {
	switch name {
	case "ascii_mode":
		return b.asciiMode
	case "full_shape":
		return b.fullShape
	default:
		return false
	}
}

func (b *testBackend) currentCommit() string {
	if len(b.candidates) > 0 {
		return b.candidates[0].Text
	}
	return strings.ReplaceAll(b.composition, "'", "")
}

func (b *testBackend) refreshCandidates() {
	code := strings.ReplaceAll(b.composition, "'", "")
	if code == "" {
		b.candidates = nil
		return
	}
	results := make([]candidateItem, 0, 9)
	seen := make(map[string]struct{})
	appendWords := func(words []candidateItem) {
		for _, word := range words {
			if _, ok := seen[word.Text]; ok {
				continue
			}
			seen[word.Text] = struct{}{}
			results = append(results, word)
			if len(results) == 9 {
				return
			}
		}
	}
	for _, entry := range testDictionary() {
		if entry.code == code {
			appendWords(entry.words)
		}
	}
	for _, entry := range testDictionary() {
		if len(results) == 9 {
			break
		}
		if entry.code != code && strings.HasPrefix(entry.code, code) {
			appendWords(entry.words)
		}
	}
	if len(results) == 0 {
		results = []candidateItem{{Text: code}}
	}
	b.candidates = results
}

func testDictionary() []testDictEntry {
	return []testDictEntry{
		{code: "ni", words: []candidateItem{{Text: "你"}, {Text: "呢"}, {Text: "泥"}, {Text: "尼"}, {Text: "拟"}}},
		{code: "nihao", words: []candidateItem{{Text: "你好"}, {Text: "你号"}, {Text: "拟好"}}},
		{code: "nimen", words: []candidateItem{{Text: "你们"}}},
		{code: "zhong", words: []candidateItem{{Text: "中"}, {Text: "种"}, {Text: "重"}}},
		{code: "zhongwen", words: []candidateItem{{Text: "中文"}}},
	}
}

func trimLastRuneForTest(s string) string {
	if s == "" {
		return s
	}
	runes := []rune(s)
	return string(runes[:len(runes)-1])
}

func newTestIME() *IME {
	return &IME{
		TextServiceBase: pime.NewTextServiceBase(&pime.Client{ID: "test-client"}),
		style: Style{
			DisplayTrayIcon:    true,
			CandidateFormat:    "{0} {1}",
			CandidatePerRow:    1,
			CandidateUseCursor: false,
			FontFace:           "MingLiu",
			FontPoint:          20,
			InlinePreedit:      "composition",
			SoftCursor:         false,
		},
		backend: newTestBackend(),
	}
}

func TestNewInitialState(t *testing.T) {
	ime := newTestIME()
	backend := ime.backend.(*testBackend)

	if !ime.style.DisplayTrayIcon {
		t.Fatal("expected tray icon style enabled by default")
	}
	if backend.composition != "" {
		t.Fatalf("expected empty composition, got %q", backend.composition)
	}
	if len(backend.candidates) != 0 {
		t.Fatalf("expected no candidates, got %v", backend.candidates)
	}
	if ime.keyComposing {
		t.Fatal("expected keyComposing to be false initially")
	}
}

func TestFilterKeyDownProcessesKeyWithoutUpdatingUI(t *testing.T) {
	ime := newTestIME()

	resp := ime.filterKeyDown(&pime.Request{
		SeqNum:   1,
		KeyCode:  0x4E,
		CharCode: 'n',
	}, pime.NewResponse(1, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected n to be handled, got %d", resp.ReturnValue)
	}
	if resp.CompositionString != "" || len(resp.CandidateList) != 0 || resp.ShowCandidates {
		t.Fatalf("expected filterKeyDown not to emit UI state, got %#v", resp)
	}
}

func TestFilterKeyDownFallsBackToKeyCodeWhenCharCodeMissing(t *testing.T) {
	ime := newTestIME()

	resp := ime.filterKeyDown(&pime.Request{
		SeqNum:  2,
		KeyCode: 0x4E,
	}, pime.NewResponse(2, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected keyCode-only N to be handled, got %d", resp.ReturnValue)
	}
}

func TestOnKeyDownReflectsBackendStateAfterFilter(t *testing.T) {
	ime := newTestIME()

	ime.filterKeyDown(&pime.Request{
		SeqNum:   1,
		KeyCode:  0x4E,
		CharCode: 'n',
	}, pime.NewResponse(1, true))
	ime.filterKeyDown(&pime.Request{
		SeqNum:   2,
		KeyCode:  0x49,
		CharCode: 'i',
	}, pime.NewResponse(2, true))

	resp := ime.onKeyDown(&pime.Request{
		SeqNum:   3,
		KeyCode:  0x49,
		CharCode: 'i',
	}, pime.NewResponse(3, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected onKeyDown to succeed, got %d", resp.ReturnValue)
	}
	if resp.CompositionString != "ni" {
		t.Fatalf("expected composition ni, got %q", resp.CompositionString)
	}
	if len(resp.CandidateList) == 0 || resp.CandidateList[0] != "你" {
		t.Fatalf("expected first exact candidate 你, got %v", resp.CandidateList)
	}
}

func TestOnKeyDownNumberSelectsCandidate(t *testing.T) {
	ime := newTestIME()
	backend := ime.backend.(*testBackend)
	backend.composition = "ni"
	backend.candidates = []candidateItem{{Text: "你"}, {Text: "呢"}, {Text: "泥"}}
	ime.keyComposing = true

	filterResp := ime.filterKeyDown(&pime.Request{
		SeqNum:  4,
		KeyCode: 0x32,
	}, pime.NewResponse(4, true))
	if filterResp.ReturnValue != 1 {
		t.Fatalf("expected number selection to be handled, got %d", filterResp.ReturnValue)
	}

	resp := ime.onKeyDown(&pime.Request{
		SeqNum:  5,
		KeyCode: 0x32,
	}, pime.NewResponse(5, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected onKeyDown after selection to succeed, got %d", resp.ReturnValue)
	}
	if resp.CommitString != "呢" {
		t.Fatalf("expected second candidate 呢, got %q", resp.CommitString)
	}
	if backend.composition != "" || backend.candidates != nil {
		t.Fatal("expected state reset after candidate selection")
	}
}

func TestOnKeyDownBackspaceUpdatesComposition(t *testing.T) {
	ime := newTestIME()
	backend := ime.backend.(*testBackend)
	backend.composition = "ni"
	backend.refreshCandidates()

	ime.filterKeyDown(&pime.Request{
		SeqNum:  5,
		KeyCode: 0x08,
	}, pime.NewResponse(5, true))
	resp := ime.onKeyDown(&pime.Request{
		SeqNum:  6,
		KeyCode: 0x08,
	}, pime.NewResponse(6, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected backspace to be handled, got %d", resp.ReturnValue)
	}
	if backend.composition != "n" {
		t.Fatalf("expected composition n after backspace, got %q", backend.composition)
	}
	if resp.CompositionString != "n" {
		t.Fatalf("expected response composition n, got %q", resp.CompositionString)
	}
	if len(resp.CandidateList) == 0 {
		t.Fatal("expected candidates to remain after backspace")
	}
}

func TestOnKeyDownEscapeClearsComposition(t *testing.T) {
	ime := newTestIME()
	backend := ime.backend.(*testBackend)
	backend.composition = "ni"
	backend.refreshCandidates()

	ime.filterKeyDown(&pime.Request{
		SeqNum:  6,
		KeyCode: 0x1B,
	}, pime.NewResponse(6, true))
	resp := ime.onKeyDown(&pime.Request{
		SeqNum:  7,
		KeyCode: 0x1B,
	}, pime.NewResponse(7, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected escape to be handled, got %d", resp.ReturnValue)
	}
	if backend.composition != "" || backend.candidates != nil {
		t.Fatal("expected composition state cleared")
	}
	if resp.CompositionString != "" || resp.ShowCandidates {
		t.Fatalf("expected cleared UI, got %#v", resp)
	}
}

func TestOnKeyDownSpaceCommitsFirstCandidate(t *testing.T) {
	ime := newTestIME()
	backend := ime.backend.(*testBackend)
	backend.composition = "ni"
	backend.refreshCandidates()

	ime.filterKeyDown(&pime.Request{
		SeqNum:  7,
		KeyCode: 0x20,
	}, pime.NewResponse(7, true))
	resp := ime.onKeyDown(&pime.Request{
		SeqNum:  8,
		KeyCode: 0x20,
	}, pime.NewResponse(8, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected space to be handled, got %d", resp.ReturnValue)
	}
	if resp.CommitString != "你" {
		t.Fatalf("expected first candidate 你, got %q", resp.CommitString)
	}
	if backend.composition != "" || backend.candidates != nil {
		t.Fatal("expected state reset after commit")
	}
}

func TestOnKeyDownPunctuationCommitsComposition(t *testing.T) {
	ime := newTestIME()
	backend := ime.backend.(*testBackend)
	backend.composition = "ni"
	backend.refreshCandidates()

	ime.filterKeyDown(&pime.Request{
		SeqNum:   8,
		KeyCode:  int('.'),
		CharCode: int('.'),
	}, pime.NewResponse(8, true))
	resp := ime.onKeyDown(&pime.Request{
		SeqNum:   9,
		KeyCode:  int('.'),
		CharCode: int('.'),
	}, pime.NewResponse(9, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected punctuation to be handled while composing, got %d", resp.ReturnValue)
	}
	if resp.CommitString != "你." {
		t.Fatalf("expected punctuation commit 你., got %q", resp.CommitString)
	}
}

func TestOnKeyDownUnhandledKeyReturnsZero(t *testing.T) {
	ime := newTestIME()

	resp := ime.filterKeyDown(&pime.Request{
		SeqNum:   9,
		KeyCode:  0x70,
		CharCode: 0,
	}, pime.NewResponse(9, true))

	if resp.ReturnValue != 0 {
		t.Fatalf("expected unrelated key to be ignored, got %d", resp.ReturnValue)
	}
}

func TestOnKeyDownAsciiModePassesThroughWhenIdle(t *testing.T) {
	ime := newTestIME()
	ime.backend.SetOption("ascii_mode", true)

	resp := ime.filterKeyDown(&pime.Request{
		SeqNum:   10,
		KeyCode:  int('A'),
		CharCode: int('a'),
	}, pime.NewResponse(10, true))

	if resp.ReturnValue != 0 {
		t.Fatalf("expected ascii mode to pass through idle typing, got %d", resp.ReturnValue)
	}
}

func TestControlKeyPassesThroughWhenIdle(t *testing.T) {
	ime := newTestIME()

	resp := ime.filterKeyDown(&pime.Request{
		SeqNum:  10,
		KeyCode: vkControl,
	}, pime.NewResponse(10, true))

	if resp.ReturnValue != 0 {
		t.Fatalf("expected bare ctrl to pass through, got %d", resp.ReturnValue)
	}
}

// Regression: if filterKeyDown does not handle a bare Ctrl key, onKeyDown must return
// unhandled as well; otherwise the host still thinks the IME consumed the modifier.
func TestOnKeyDownBareControlUnhandledWhenFilterDoesNotHandle(t *testing.T) {
	ime := newTestIME()
	const seq = 20
	filterResp := ime.filterKeyDown(&pime.Request{
		SeqNum:  seq,
		KeyCode: vkControl,
	}, pime.NewResponse(seq, true))
	if filterResp.ReturnValue != 0 {
		t.Fatalf("expected filterKeyDown bare Ctrl unhandled, got %d", filterResp.ReturnValue)
	}
	onResp := ime.onKeyDown(&pime.Request{
		SeqNum:  seq + 1,
		KeyCode: vkControl,
	}, pime.NewResponse(seq+1, true))
	if onResp.ReturnValue != 0 {
		t.Fatalf("expected onKeyDown bare Ctrl unhandled when filter did not handle, got %d", onResp.ReturnValue)
	}
}

func TestOnKeyDownControlShortcutUnhandledWhenFilterDoesNotHandle(t *testing.T) {
	ime := newTestIME()
	const seq = 22
	filterResp := ime.filterKeyDown(&pime.Request{
		SeqNum:   seq,
		KeyCode:  int('A'),
		CharCode: 1,
	}, pime.NewResponse(seq, true))
	if filterResp.ReturnValue != 0 {
		t.Fatalf("expected filterKeyDown ctrl+a unhandled, got %d", filterResp.ReturnValue)
	}
	onResp := ime.onKeyDown(&pime.Request{
		SeqNum:   seq + 1,
		KeyCode:  int('A'),
		CharCode: 1,
	}, pime.NewResponse(seq+1, true))
	if onResp.ReturnValue != 0 {
		t.Fatalf("expected onKeyDown ctrl+a unhandled when filter did not handle, got %d", onResp.ReturnValue)
	}
}

// Regression: same contract as TestOnKeyDownBareControlUnhandledWhenFilterDoesNotHandle for key-up / Alt.
func TestOnKeyUpBareAltUnhandledWhenFilterDoesNotHandle(t *testing.T) {
	ime := newTestIME()
	const seq = 21
	filterResp := ime.filterKeyUp(&pime.Request{
		SeqNum:  seq,
		KeyCode: vkMenu,
	}, pime.NewResponse(seq, true))
	if filterResp.ReturnValue != 0 {
		t.Fatalf("expected filterKeyUp bare Alt unhandled, got %d", filterResp.ReturnValue)
	}
	onResp := ime.onKeyUp(&pime.Request{
		SeqNum:  seq + 1,
		KeyCode: vkMenu,
	}, pime.NewResponse(seq+1, true))
	if onResp.ReturnValue != 0 {
		t.Fatalf("expected onKeyUp bare Alt unhandled when filter did not handle, got %d", onResp.ReturnValue)
	}
}

func TestOnCommandHandlesKnownAndMissingCommand(t *testing.T) {
	ime := newTestIME()
	backend := ime.backend.(*testBackend)
	backend.composition = "ni"
	backend.refreshCandidates()

	validResp := ime.onCommand(&pime.Request{
		SeqNum: 11,
		ID:     pime.FlexibleID{Int: ID_ASCII_MODE, IsInt: true},
	}, pime.NewResponse(11, true))
	if validResp.ReturnValue != 1 {
		t.Fatalf("expected known command to be handled, got %d", validResp.ReturnValue)
	}
	if !ime.backend.GetOption("ascii_mode") {
		t.Fatal("expected ascii mode toggled on")
	}
	if backend.composition != "ni" {
		t.Fatalf("expected test composition preserved until backend handles key flow, got %q", backend.composition)
	}

	missingResp := ime.onCommand(&pime.Request{
		SeqNum: 12,
	}, pime.NewResponse(12, true))
	if missingResp.ReturnValue != 0 {
		t.Fatalf("expected missing commandId to be ignored, got %d", missingResp.ReturnValue)
	}
}

func TestOnMenuReturnsSettingsMenu(t *testing.T) {
	ime := newTestIME()

	resp := ime.onMenu(&pime.Request{
		SeqNum: 15,
		ID:     pime.FlexibleID{String: "settings"},
	}, pime.NewResponse(15, true))

	items, ok := resp.ReturnData.([]map[string]interface{})
	if !ok || len(items) == 0 {
		t.Fatalf("expected settings menu items, got %#v", resp.ReturnData)
	}
	if text, ok := items[0]["text"].(string); !ok || text == "" {
		t.Fatalf("expected first menu item text, got %#v", items[0])
	}
}

func TestHandleRequestCompositionTerminatedResetsState(t *testing.T) {
	ime := newTestIME()
	backend := ime.backend.(*testBackend)
	backend.composition = "ni"
	backend.refreshCandidates()

	resp := ime.HandleRequest(&pime.Request{
		SeqNum: 13,
		Method: "onCompositionTerminated",
	})

	if !resp.Success {
		t.Fatal("expected composition termination response to succeed")
	}
	if backend.composition != "" || backend.candidates != nil {
		t.Fatal("expected state reset on composition termination")
	}
}

func TestHandleRequestOnDeactivateReturnsHandled(t *testing.T) {
	ime := newTestIME()
	backend := ime.backend.(*testBackend)
	backend.composition = "ni"
	backend.refreshCandidates()

	resp := ime.HandleRequest(&pime.Request{
		SeqNum: 14,
		Method: "onDeactivate",
	})

	if resp.ReturnValue != 1 {
		t.Fatalf("expected onDeactivate to return 1, got %d", resp.ReturnValue)
	}
	if backend.composition != "" || backend.candidates != nil {
		t.Fatal("expected deactivate to clear composition state")
	}
}
