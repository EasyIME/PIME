//go:build windows

package rime

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/EasyIME/pime-go/pime"
)

func newRealRimeSession(t *testing.T) RimeSessionId {
	t.Helper()

	wd := "D:\\vscode\\moqi-input-method-projs\\PIME\\go-backend\\input_methods\\rime"
	appData := os.Getenv("APPDATA")
	if appData == "" {
		t.Skip("APPDATA is not set")
	}
	userDir := filepath.Join(appData, APP, "Rime")
	if info, err := os.Stat(userDir); err != nil || !info.IsDir() {
		t.Skip("existing user Rime directory is required")
	}
	dataDir := filepath.Join(wd, "data")

	if !RimeInit(dataDir, userDir, APP, APP_VERSION, false) {
		t.Fatal("RimeInit failed")
	}

	sessionID, ok := StartSession()
	if !ok || sessionID == 0 {
		t.Fatal("StartSession failed")
	}
	t.Cleanup(func() {
		EndSession(sessionID)
		Finalize()
	})
	t.Logf("ascii_mode before typing: %t", GetOption(sessionID, "ascii_mode"))
	t.Logf("full_shape before typing: %t", GetOption(sessionID, "full_shape"))
	SetOption(sessionID, "ascii_mode", false)
	t.Logf("ascii_mode after forcing off: %t", GetOption(sessionID, "ascii_mode"))
	return sessionID
}

func TestRealRimeCanCommitText(t *testing.T) {
	sessionID := newRealRimeSession(t)

	for _, input := range []string{"nihao", "xpxp", "gegegojxyzgegegojxdegoge"} {
		t.Run(input, func(t *testing.T) {
			ClearComposition(sessionID)
			for _, key := range []rune(input) {
				if !ProcessKey(sessionID, int(key), 0) {
					if composition, ok := GetComposition(sessionID); ok {
						t.Logf("composition after failed %q: %#v", key, composition)
					}
					if menu, ok := GetMenu(sessionID); ok {
						t.Logf("menu after failed %q: %#v", key, menu)
					}
					t.Fatalf("ProcessKey failed for %q", key)
				}
			}

			menu, ok := GetMenu(sessionID)
			if !ok || len(menu.Candidates) == 0 {
				t.Fatalf("expected candidates after %s, got %#v", input, menu)
			}
			t.Logf("candidates after %s: %#v", input, menu.Candidates)

			if !ProcessKey(sessionID, int(' '), 0) {
				t.Fatal("ProcessKey failed for space")
			}

			commit, ok := GetCommit(sessionID)
			if !ok {
				t.Fatal("expected commit after space")
			}
			t.Logf("commit text for %s: %q", input, commit.Text)

			if commit.Text == "" || commit.Text == input {
				t.Fatalf("expected converted text commit for %s, got %q", input, commit.Text)
			}
		})
	}
}

func TestRealRimeControlShortcuts(t *testing.T) {
	sessionID := newRealRimeSession(t)

	tests := []struct {
		name string
		req  *pime.Request
	}{
		{
			name: "ctrl+a",
			req: &pime.Request{
				KeyCode:   'A',
				CharCode:  1,
				KeyStates: keyStatesDown(vkControl),
			},
		},
		{
			name: "ctrl+grave",
			req: &pime.Request{
				KeyCode:   0xC0,
				CharCode:  '`',
				KeyStates: keyStatesDown(vkControl),
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			ClearComposition(sessionID)

			translatedKey := translateKeyCode(tc.req)
			modifiers := translateModifiers(tc.req, false)
			handled := ProcessKey(sessionID, translatedKey, modifiers)

			t.Logf("request: keyCode=%d charCode=%d translatedKey=%d modifiers=%d handled=%t",
				tc.req.KeyCode, tc.req.CharCode, translatedKey, modifiers, handled)

			if composition, ok := GetComposition(sessionID); ok {
				t.Logf("composition: %#v", composition)
			} else {
				t.Log("composition: <none>")
			}

			if menu, ok := GetMenu(sessionID); ok {
				t.Logf("menu: %#v", menu)
			} else {
				t.Log("menu: <none>")
			}

			if commit, ok := GetCommit(sessionID); ok {
				t.Logf("commit: %#v", commit)
			} else {
				t.Log("commit: <none>")
			}
		})
	}
}

func TestRealRimeBackspaceUpdatesComposition(t *testing.T) {
	sessionID := newRealRimeSession(t)
	ClearComposition(sessionID)

	typeASCII(t, sessionID, "ni")
	before, ok := GetComposition(sessionID)
	if !ok || before.Preedit == "" {
		t.Fatalf("expected composition before backspace, got %#v", before)
	}

	handled := processRealKey(sessionID, &pime.Request{KeyCode: vkBack})
	after, ok := GetComposition(sessionID)
	if !handled {
		t.Fatal("expected backspace to be handled")
	}
	if !ok || after.Preedit == "" {
		t.Fatalf("expected composition to remain after backspace, got %#v", after)
	}
	if len([]rune(after.Preedit)) >= len([]rune(before.Preedit)) {
		t.Fatalf("expected shorter composition after backspace, before=%q after=%q", before.Preedit, after.Preedit)
	}
	if menu, ok := GetMenu(sessionID); !ok || len(menu.Candidates) == 0 {
		t.Fatalf("expected candidates to remain after backspace, got %#v", menu)
	}
}

func TestRealRimeEscapeClearsComposition(t *testing.T) {
	sessionID := newRealRimeSession(t)
	ClearComposition(sessionID)

	typeASCII(t, sessionID, "ni")
	if composition, ok := GetComposition(sessionID); !ok || composition.Preedit == "" {
		t.Fatalf("expected composition before escape, got %#v", composition)
	}

	handled := processRealKey(sessionID, &pime.Request{KeyCode: vkEscape})
	composition, compositionOK := GetComposition(sessionID)
	menu, menuOK := GetMenu(sessionID)
	if !handled {
		t.Fatal("expected escape to be handled")
	}
	if !compositionOK || composition.Preedit != "" {
		t.Fatalf("expected escape to clear composition, got %#v", composition)
	}
	if menuOK && len(menu.Candidates) != 0 {
		t.Fatalf("expected escape to clear candidates, got %#v", menu)
	}
}

func TestRealRimePunctuationKeys(t *testing.T) {
	sessionID := newRealRimeSession(t)

	tests := []struct {
		name          string
		req           *pime.Request
		allowedCommit []string
	}{
		{
			name: "grave",
			req: &pime.Request{
				KeyCode:  0xC0,
				CharCode: '`',
			},
			allowedCommit: []string{"、", "`", "｀"},
		},
		{
			name: "pipe",
			req: &pime.Request{
				KeyCode:  0xDC,
				CharCode: '|',
			},
			allowedCommit: []string{"|", "·", "｜"},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			ClearComposition(sessionID)

			handled := processRealKey(sessionID, tc.req)
			commit, commitOK := GetCommit(sessionID)
			composition, compositionOK := GetComposition(sessionID)
			menu, menuOK := GetMenu(sessionID)

			t.Logf("request=%s handled=%t commit=%#v composition=%#v menu=%#v", tc.name, handled, commit, composition, menu)

			if !handled {
				t.Fatalf("expected %s key to be handled", tc.name)
			}
			if commitOK && commit.Text != "" {
				if !containsAny(tc.allowedCommit, commit.Text) {
					t.Fatalf("unexpected commit for %s: %q", tc.name, commit.Text)
				}
				return
			}
			if compositionOK && composition.Preedit != "" {
				return
			}
			if menuOK && len(menu.Candidates) > 0 {
				return
			}
			t.Fatalf("expected %s key to produce visible output", tc.name)
		})
	}
}

func keyStatesDown(codes ...int) pime.KeyStates {
	states := make(pime.KeyStates, 256)
	for _, code := range codes {
		if code >= 0 && code < len(states) {
			states[code] = 1 << 7
		}
	}
	return states
}

func processRealKey(sessionID RimeSessionId, req *pime.Request) bool {
	return ProcessKey(sessionID, translateKeyCode(req), translateModifiers(req, false))
}

func typeASCII(t *testing.T, sessionID RimeSessionId, input string) {
	t.Helper()
	for _, key := range input {
		if !ProcessKey(sessionID, int(key), 0) {
			t.Fatalf("ProcessKey failed for %q", key)
		}
	}
}

func containsAny(candidates []string, got string) bool {
	for _, candidate := range candidates {
		if strings.Contains(got, candidate) {
			return true
		}
	}
	return false
}
