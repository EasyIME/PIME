//go:build windows

package rime

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"testing"

	"github.com/EasyIME/pime-go/pime"
)

// The runtime tests drive the bundled x64 rime.dll against the real
// luna_pinyin data from the brise submodule shared with the python side: a
// genuine schema and dictionary, no fabricated fixtures. The schema_list in
// the user dir is patched down to luna_pinyin so the first RimeInit only
// compiles that one schema; librime caches the build, so every later test
// reuses it. librime's engine is a process-global singleton, so the shared
// and user directories are built once for the whole package.
var (
	rimeEnvOnce  sync.Once
	rimeEnvErr   error
	rimeShared   string
	rimeUser     string
)

func setupRimeEnv() (shared, user string, err error) {
	// The bundled rime.dll is x64; a native arm64 process cannot load it.
	// amd64 is the default on Intel hosts and runs emulated on ARM64 Windows.
	if runtime.GOARCH == "arm64" {
		return "", "", fmt.Errorf("bundled x64 rime.dll needs an amd64 test process: run with GOARCH=amd64")
	}

	// Both variables set selects a pre-built pair (e.g. the real
	// %APPDATA%\PIME\Rime data for a live-data run); otherwise they are
	// assembled per package under %TEMP% and never touch user data.
	shared, user = os.Getenv("PIME_TEST_SHARED_DIR"), os.Getenv("PIME_TEST_RIME_USER_DIR")
	if shared != "" && user != "" {
		return shared, user, nil
	}

	brise, err := filepath.Abs(filepath.Join("..", "..", "..", "python", "input_methods", "rime", "brise"))
	if err != nil {
		return "", "", err
	}
	if _, err := os.Stat(filepath.Join(brise, "preset", "luna_pinyin.dict.yaml")); err != nil {
		return "", "", fmt.Errorf("brise submodule not initialised: run git submodule update --init python/input_methods/rime/brise")
	}

	if shared == "" {
		if shared, err = os.MkdirTemp("", "pime-rime-shared-*"); err != nil {
			return "", "", err
		}
		for _, name := range []string{"default.yaml", "essay.txt", "symbols.yaml"} {
			if err := copyRimeFile(filepath.Join(brise, name), filepath.Join(shared, name)); err != nil {
				return "", "", err
			}
		}
		if err := copyRimeTree(filepath.Join(brise, "opencc"), filepath.Join(shared, "opencc")); err != nil {
			return "", "", err
		}
		for _, name := range []string{"luna_pinyin.schema.yaml", "luna_pinyin.dict.yaml"} {
			if err := copyRimeFile(filepath.Join(brise, "preset", name), filepath.Join(shared, name)); err != nil {
				return "", "", err
			}
		}
	}

	// The product reads %APPDATA%\PIME\Rime; tests never write there.
	if user == "" {
		if user, err = os.MkdirTemp("", "pime-rime-user-*"); err != nil {
			return "", "", err
		}
		patch := "patch:\n  schema_list:\n    - schema: luna_pinyin\n"
		if err := os.WriteFile(filepath.Join(user, "default.custom.yaml"), []byte(patch), 0o644); err != nil {
			return "", "", err
		}
	}
	return shared, user, nil
}

func copyRimeFile(src, dst string) error {
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dst, data, 0o644)
}

func copyRimeTree(src, dst string) error {
	return filepath.WalkDir(src, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		target := filepath.Join(dst, rel)
		if d.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		return copyRimeFile(path, target)
	})
}

func newRealRimeSession(t *testing.T) RimeSessionId {
	t.Helper()

	rimeEnvOnce.Do(func() { rimeShared, rimeUser, rimeEnvErr = setupRimeEnv() })
	if rimeEnvErr != nil {
		t.Skip(rimeEnvErr.Error())
	}

	if !RimeInit(rimeShared, rimeUser, APP, APP_VERSION, false) {
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

	for _, input := range []string{"nihao", "xiexie", "shurufa", "ceshi"} {
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
