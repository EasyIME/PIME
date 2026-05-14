package meow

import (
	"testing"

	"github.com/EasyIME/pime-go/pime"
)

func newTestIME() *IME {
	return New(&pime.Client{ID: "test-client"}).(*IME)
}

func TestNewInitialState(t *testing.T) {
	ime := newTestIME()

	if ime.compositionString != "" {
		t.Fatalf("expected empty composition, got %q", ime.compositionString)
	}
	if ime.showCandidates {
		t.Fatal("expected candidates to be hidden initially")
	}
	if ime.candidateCursor != 0 {
		t.Fatalf("expected candidate cursor 0, got %d", ime.candidateCursor)
	}
}

func TestFilterKeyDownWhenCompositionEmpty(t *testing.T) {
	ime := newTestIME()

	tests := []struct {
		name    string
		keyCode int
		charCode int
		want    int
	}{
		{name: "enter is ignored", keyCode: 0x0D, want: 0},
		{name: "backspace is ignored", keyCode: 0x08, want: 0},
		{name: "left is ignored", keyCode: 0x25, want: 0},
		{name: "up is ignored", keyCode: 0x26, want: 0},
		{name: "down is ignored when empty", keyCode: 0x28, want: 0},
		{name: "right is ignored", keyCode: 0x27, want: 0},
		{name: "shift is ignored", keyCode: 0x10, want: 0},
		{name: "letter is handled", keyCode: 0x4D, charCode: 'm', want: 1},
		{name: "other printable letter is handled", keyCode: 0x46, charCode: 'f', want: 1},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			resp := ime.filterKeyDown(&pime.Request{KeyCode: tt.keyCode, CharCode: tt.charCode}, pime.NewResponse(1, true))
			if resp.ReturnValue != tt.want {
				t.Fatalf("expected returnValue %d, got %d", tt.want, resp.ReturnValue)
			}
		})
	}
}

func TestFilterKeyDownWhenCompositionExists(t *testing.T) {
	ime := newTestIME()
	ime.compositionString = "喵"

	resp := ime.filterKeyDown(&pime.Request{KeyCode: 0x0D}, pime.NewResponse(1, true))
	if resp.ReturnValue != 1 {
		t.Fatalf("expected enter to be handled while composing, got %d", resp.ReturnValue)
	}
}

func TestOnKeyDownFirstMStartsComposition(t *testing.T) {
	ime := newTestIME()

	resp := ime.onKeyDown(&pime.Request{SeqNum: 1, CharCode: 'm', KeyCode: 0x4D}, pime.NewResponse(1, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected first m to be handled, got %d", resp.ReturnValue)
	}
	if resp.CompositionString != "喵" {
		t.Fatalf("expected composition 喵, got %q", resp.CompositionString)
	}
	if resp.ShowCandidates {
		t.Fatal("expected candidates to stay hidden on first m")
	}
	if ime.compositionString != "喵" {
		t.Fatalf("expected ime state to store 喵, got %q", ime.compositionString)
	}
}

func TestOnKeyDownUppercaseMAlsoStartsComposition(t *testing.T) {
	ime := newTestIME()

	resp := ime.onKeyDown(&pime.Request{SeqNum: 1, CharCode: 'M', KeyCode: 0x4D}, pime.NewResponse(1, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected uppercase M to be handled, got %d", resp.ReturnValue)
	}
	if resp.CompositionString != "喵" {
		t.Fatalf("expected composition 喵, got %q", resp.CompositionString)
	}
}

func TestOnKeyDownFallsBackToKeyCodeWhenCharCodeMissing(t *testing.T) {
	ime := newTestIME()

	resp := ime.onKeyDown(&pime.Request{SeqNum: 1, KeyCode: 0x4D}, pime.NewResponse(1, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected keyCode-only M to be handled, got %d", resp.ReturnValue)
	}
	if resp.CompositionString != "喵" {
		t.Fatalf("expected composition 喵 from keyCode fallback, got %q", resp.CompositionString)
	}
}

func TestOnKeyDownSecondMShowsCandidates(t *testing.T) {
	ime := newTestIME()
	ime.compositionString = "喵"

	resp := ime.onKeyDown(&pime.Request{SeqNum: 2, CharCode: 'm', KeyCode: 0x4D}, pime.NewResponse(2, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected second m to be handled, got %d", resp.ReturnValue)
	}
	if resp.CompositionString != "喵" {
		t.Fatalf("expected composition to remain 喵, got %q", resp.CompositionString)
	}
	if !resp.ShowCandidates {
		t.Fatal("expected candidates to be shown on repeated m")
	}
	if len(resp.CandidateList) != len(candidates) {
		t.Fatalf("expected %d candidates, got %d", len(candidates), len(resp.CandidateList))
	}
	for i, candidate := range candidates {
		if resp.CandidateList[i] != candidate {
			t.Fatalf("candidate %d mismatch: want %q, got %q", i, candidate, resp.CandidateList[i])
		}
	}
	if !ime.showCandidates {
		t.Fatal("expected ime state to track candidate visibility")
	}
}

func TestOnKeyDownNumberSelectsCandidate(t *testing.T) {
	ime := newTestIME()
	ime.compositionString = "喵"
	ime.showCandidates = true

	resp := ime.onKeyDown(&pime.Request{SeqNum: 3, KeyCode: 0x32}, pime.NewResponse(3, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected number key to be handled, got %d", resp.ReturnValue)
	}
	if resp.CommitString != "描" {
		t.Fatalf("expected second candidate 描, got %q", resp.CommitString)
	}
	if resp.CompositionString != "" {
		t.Fatalf("expected composition to be cleared, got %q", resp.CompositionString)
	}
	if resp.ShowCandidates {
		t.Fatal("expected candidates to be hidden after commit")
	}
	if ime.compositionString != "" || ime.showCandidates {
		t.Fatal("expected ime state to reset after candidate selection")
	}
}

func TestOnKeyDownEnterCommitsComposition(t *testing.T) {
	ime := newTestIME()
	ime.compositionString = "喵"
	ime.showCandidates = true

	resp := ime.onKeyDown(&pime.Request{SeqNum: 4, KeyCode: 0x0D}, pime.NewResponse(4, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected enter to be handled, got %d", resp.ReturnValue)
	}
	if resp.CommitString != "喵" {
		t.Fatalf("expected enter to commit 喵, got %q", resp.CommitString)
	}
	if resp.CompositionString != "" {
		t.Fatalf("expected composition to clear, got %q", resp.CompositionString)
	}
	if resp.ShowCandidates {
		t.Fatal("expected candidates to be hidden after enter")
	}
	if ime.compositionString != "" || ime.showCandidates {
		t.Fatal("expected ime state to reset after enter")
	}
}

func TestOnKeyDownBackspaceClearsComposition(t *testing.T) {
	ime := newTestIME()
	ime.compositionString = "喵喵"
	ime.showCandidates = true

	resp := ime.onKeyDown(&pime.Request{SeqNum: 5, KeyCode: 0x08}, pime.NewResponse(5, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected backspace to be handled, got %d", resp.ReturnValue)
	}
	if resp.CompositionString != "喵" {
		t.Fatalf("expected composition to shrink, got %q", resp.CompositionString)
	}
	if resp.ShowCandidates {
		t.Fatal("expected candidates to be hidden after backspace")
	}
	if ime.compositionString != "喵" || ime.showCandidates {
		t.Fatal("expected ime state to keep remaining composition after backspace")
	}
}

func TestOnKeyDownEscapeCancelsComposition(t *testing.T) {
	ime := newTestIME()
	ime.compositionString = "喵"
	ime.showCandidates = true

	resp := ime.onKeyDown(&pime.Request{SeqNum: 6, KeyCode: 0x1B}, pime.NewResponse(6, true))

	if resp.ReturnValue != 1 {
		t.Fatalf("expected escape to be handled, got %d", resp.ReturnValue)
	}
	if resp.CompositionString != "喵" {
		t.Fatalf("expected composition to remain while closing candidate list, got %q", resp.CompositionString)
	}
	if resp.ShowCandidates {
		t.Fatal("expected candidates to be hidden after escape")
	}
	if ime.compositionString != "喵" || ime.showCandidates {
		t.Fatal("expected ime state to keep composition but hide candidates after escape")
	}
}

func TestOnKeyDownUnhandledKeyReturnsZero(t *testing.T) {
	ime := newTestIME()

	resp := ime.onKeyDown(&pime.Request{SeqNum: 7, KeyCode: 0x10}, pime.NewResponse(7, true))
	if resp.ReturnValue != 0 {
		t.Fatalf("expected modifier key to be ignored, got %d", resp.ReturnValue)
	}
}

func TestOnKeyDownOtherPrintableKeyAlsoBuildsComposition(t *testing.T) {
	ime := newTestIME()

	resp := ime.onKeyDown(&pime.Request{SeqNum: 8, KeyCode: 0x46, CharCode: 'f'}, pime.NewResponse(8, true))
	if resp.ReturnValue != 1 {
		t.Fatalf("expected printable key to be handled, got %d", resp.ReturnValue)
	}
	if resp.CompositionString != "喵" {
		t.Fatalf("expected printable key to append 喵, got %q", resp.CompositionString)
	}
}

func TestOnKeyDownBackspaceRemovesLastRune(t *testing.T) {
	ime := newTestIME()
	ime.compositionString = "喵喵"
	ime.showCandidates = true

	resp := ime.onKeyDown(&pime.Request{SeqNum: 9, KeyCode: 0x08}, pime.NewResponse(9, true))
	if resp.ReturnValue != 1 {
		t.Fatalf("expected backspace to be handled, got %d", resp.ReturnValue)
	}
	if resp.CompositionString != "喵" {
		t.Fatalf("expected composition to shrink to one rune, got %q", resp.CompositionString)
	}
	if ime.compositionString != "喵" {
		t.Fatalf("expected ime composition to shrink, got %q", ime.compositionString)
	}
}

func TestHandleRequestCompositionTerminatedResetsState(t *testing.T) {
	ime := newTestIME()
	ime.compositionString = "喵"
	ime.showCandidates = true
	ime.candidateCursor = 2

	resp := ime.HandleRequest(&pime.Request{SeqNum: 8, Method: "onCompositionTerminated"})

	if !resp.Success {
		t.Fatal("expected composition termination response to succeed")
	}
	if ime.compositionString != "" {
		t.Fatalf("expected composition to reset, got %q", ime.compositionString)
	}
	if ime.showCandidates {
		t.Fatal("expected candidates to reset")
	}
	if ime.candidateCursor != 0 {
		t.Fatalf("expected cursor to reset, got %d", ime.candidateCursor)
	}
}
