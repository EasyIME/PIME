package main

import (
	"encoding/json"
	"io"
	"os"
	"strings"
	"testing"

	fcitx5ime "github.com/EasyIME/pime-go/input_methods/fcitx5"
	meowime "github.com/EasyIME/pime-go/input_methods/meow"
	rimeime "github.com/EasyIME/pime-go/input_methods/rime"
	simplepinyinime "github.com/EasyIME/pime-go/input_methods/simple_pinyin"
	"github.com/EasyIME/pime-go/pime"
)

const testMeowGUID = "{7A1C2E93-5B64-4F88-AE21-3D9C6B70F145}"
const testSimplePinyinGUID = "{5C8E1D74-2F9A-4B63-91DE-7A45C8F2B306}"
const testRimeGUID = "{3F6B5A12-8D44-4E71-9A2E-6B4F9C1D2A30}"
const testFcitx5GUID = "{D2E4A8B1-6C35-4F90-AB7D-18E2635C9F41}"

func newTestServerWithMeow() *Server {
	server := NewServer()
	server.RegisterService(testMeowGUID, func(client *pime.Client, guid string) pime.TextService {
		return meowime.New(client)
	})
	return server
}

func newTestServerWithSimplePinyin() *Server {
	server := NewServer()
	server.RegisterService(testSimplePinyinGUID, func(client *pime.Client, guid string) pime.TextService {
		return simplepinyinime.New(client)
	})
	return server
}

func newTestServerWithRime() *Server {
	server := NewServer()
	server.RegisterService(testRimeGUID, func(client *pime.Client, guid string) pime.TextService {
		return rimeime.New(client)
	})
	return server
}

func newTestServerWithFcitx5() *Server {
	server := NewServer()
	server.RegisterService(testFcitx5GUID, func(client *pime.Client, guid string) pime.TextService {
		return fcitx5ime.New(client)
	})
	return server
}

func captureStdout(t *testing.T, fn func()) string {
	t.Helper()

	oldStdout := os.Stdout
	reader, writer, err := os.Pipe()
	if err != nil {
		t.Fatalf("create stdout pipe: %v", err)
	}

	os.Stdout = writer
	defer func() {
		os.Stdout = oldStdout
	}()

	fn()

	if err := writer.Close(); err != nil {
		t.Fatalf("close stdout writer: %v", err)
	}

	output, err := io.ReadAll(reader)
	if err != nil {
		t.Fatalf("read captured stdout: %v", err)
	}
	if err := reader.Close(); err != nil {
		t.Fatalf("close stdout reader: %v", err)
	}

	return strings.TrimSpace(string(output))
}

func sendProtocolMessage(t *testing.T, server *Server, clientID string, payload map[string]interface{}) (string, map[string]interface{}) {
	t.Helper()

	data, err := json.Marshal(payload)
	if err != nil {
		t.Fatalf("marshal payload: %v", err)
	}

	line := clientID + "|" + string(data)
	output := captureStdout(t, func() {
		if err := server.handleMessage(line); err != nil {
			t.Fatalf("handleMessage failed: %v", err)
		}
	})

	prefix := pime.MsgPIME + "|" + clientID + "|"
	if !strings.HasPrefix(output, prefix) {
		t.Fatalf("expected %q prefix, got %q", prefix, output)
	}

	var response map[string]interface{}
	if err := json.Unmarshal([]byte(strings.TrimPrefix(output, prefix)), &response); err != nil {
		t.Fatalf("unmarshal response: %v", err)
	}

	return output, response
}

func TestServerHandleMessageInitUsesTopLevelID(t *testing.T) {
	server := newTestServerWithMeow()

	_, response := sendProtocolMessage(t, server, "client-1", map[string]interface{}{
		"method":          "init",
		"seqNum":          1,
		"id":              testMeowGUID,
		"isWindows8Above": true,
		"isMetroApp":      false,
		"isUiLess":        false,
		"isConsole":       false,
	})

	if response["success"] != true {
		t.Fatalf("expected init success, got %#v", response)
	}
	if response["seqNum"] != float64(1) {
		t.Fatalf("expected seqNum 1, got %#v", response["seqNum"])
	}

	client := server.clients["client-1"]
	if client == nil {
		t.Fatal("expected client to be registered after init")
	}
	if client.GUID != strings.ToLower(testMeowGUID) {
		t.Fatalf("expected guid %q, got %q", strings.ToLower(testMeowGUID), client.GUID)
	}
}

func TestServerHandleMessageInitAcceptsLowercaseGUID(t *testing.T) {
	server := newTestServerWithMeow()

	_, response := sendProtocolMessage(t, server, "client-lower", map[string]interface{}{
		"method":          "init",
		"seqNum":          1,
		"id":              strings.ToLower(testMeowGUID),
		"isWindows8Above": true,
		"isMetroApp":      false,
		"isUiLess":        false,
		"isConsole":       false,
	})

	if response["success"] != true {
		t.Fatalf("expected lowercase guid init success, got %#v", response)
	}
}

func TestServerHandleMessageMeowRequestResponseFlow(t *testing.T) {
	server := newTestServerWithMeow()

	sendProtocolMessage(t, server, "client-2", map[string]interface{}{
		"method":          "init",
		"seqNum":          1,
		"id":              testMeowGUID,
		"isWindows8Above": true,
		"isMetroApp":      false,
		"isUiLess":        false,
		"isConsole":       false,
	})

	_, filterResp := sendProtocolMessage(t, server, "client-2", map[string]interface{}{
		"method":   "filterKeyDown",
		"seqNum":   2,
		"keyCode":  0x4D,
		"charCode": 'm',
	})
	if filterResp["return"] != float64(1) {
		t.Fatalf("expected filterKeyDown to handle m, got %#v", filterResp)
	}

	_, firstKeyResp := sendProtocolMessage(t, server, "client-2", map[string]interface{}{
		"method":   "onKeyDown",
		"seqNum":   3,
		"keyCode":  0x4D,
		"charCode": 'm',
	})
	if firstKeyResp["compositionString"] != "喵" {
		t.Fatalf("expected first m to build composition 喵, got %#v", firstKeyResp)
	}
	if firstKeyResp["return"] != float64(1) {
		t.Fatalf("expected first m return 1, got %#v", firstKeyResp)
	}

	_, secondKeyResp := sendProtocolMessage(t, server, "client-2", map[string]interface{}{
		"method":   "onKeyDown",
		"seqNum":   4,
		"keyCode":  0x4D,
		"charCode": 'm',
	})
	if secondKeyResp["showCandidates"] != true {
		t.Fatalf("expected second m to show candidates, got %#v", secondKeyResp)
	}
	candidateList, ok := secondKeyResp["candidateList"].([]interface{})
	if !ok {
		t.Fatalf("expected candidate list array, got %#v", secondKeyResp["candidateList"])
	}
	if len(candidateList) != 4 {
		t.Fatalf("expected 4 candidates, got %d", len(candidateList))
	}
	if candidateList[1] != "描" {
		t.Fatalf("expected second candidate 描, got %#v", candidateList[1])
	}

	_, selectResp := sendProtocolMessage(t, server, "client-2", map[string]interface{}{
		"method":  "onKeyDown",
		"seqNum":  5,
		"keyCode": 0x32,
	})
	if selectResp["commitString"] != "描" {
		t.Fatalf("expected number key to commit 描, got %#v", selectResp)
	}
	if selectResp["showCandidates"] != false {
		t.Fatalf("expected candidate window to close, got %#v", selectResp)
	}
	if selectResp["return"] != float64(1) {
		t.Fatalf("expected candidate selection return 1, got %#v", selectResp)
	}
}

func TestServerHandleMessageUninitializedClientReturnsProtocolError(t *testing.T) {
	server := newTestServerWithMeow()

	_, response := sendProtocolMessage(t, server, "client-3", map[string]interface{}{
		"method":   "onKeyDown",
		"seqNum":   9,
		"keyCode":  0x4D,
		"charCode": 'm',
	})

	if response["success"] != false {
		t.Fatalf("expected uninitialized client to fail, got %#v", response)
	}
	if response["seqNum"] != float64(9) {
		t.Fatalf("expected seqNum 9, got %#v", response["seqNum"])
	}
	if response["error"] != "客户端未初始化" {
		t.Fatalf("expected protocol error for uninitialized client, got %#v", response["error"])
	}
}

func TestServerHandleMessageCloseSucceeds(t *testing.T) {
	server := newTestServerWithMeow()

	sendProtocolMessage(t, server, "client-close", map[string]interface{}{
		"method":          "init",
		"seqNum":          1,
		"id":              testMeowGUID,
		"isWindows8Above": true,
		"isMetroApp":      false,
		"isUiLess":        false,
		"isConsole":       false,
	})

	_, response := sendProtocolMessage(t, server, "client-close", map[string]interface{}{
		"method": "close",
		"seqNum": 2,
	})

	if response["success"] != true {
		t.Fatalf("expected close success, got %#v", response)
	}
	if _, ok := server.clients["client-close"]; ok {
		t.Fatal("expected client to be removed after close")
	}
}

func TestServerHandleMessageSimplePinyinRequestResponseFlow(t *testing.T) {
	server := newTestServerWithSimplePinyin()

	sendProtocolMessage(t, server, "client-4", map[string]interface{}{
		"method":          "init",
		"seqNum":          1,
		"id":              testSimplePinyinGUID,
		"isWindows8Above": true,
		"isMetroApp":      false,
		"isUiLess":        false,
		"isConsole":       false,
	})

	_, firstResp := sendProtocolMessage(t, server, "client-4", map[string]interface{}{
		"method":   "filterKeyDown",
		"seqNum":   2,
		"keyCode":  0x4E,
		"charCode": 'n',
	})
	if firstResp["compositionString"] != "n" {
		t.Fatalf("expected first key to build composition n, got %#v", firstResp)
	}
	if firstResp["return"] != float64(1) {
		t.Fatalf("expected first key return 1, got %#v", firstResp)
	}

	_, secondResp := sendProtocolMessage(t, server, "client-4", map[string]interface{}{
		"method":   "filterKeyDown",
		"seqNum":   3,
		"keyCode":  0x49,
		"charCode": 'i',
	})
	if secondResp["compositionString"] != "ni" {
		t.Fatalf("expected second key to build composition ni, got %#v", secondResp)
	}
	candidateList, ok := secondResp["candidateList"].([]interface{})
	if !ok {
		t.Fatalf("expected candidate list array, got %#v", secondResp["candidateList"])
	}
	if len(candidateList) != 3 {
		t.Fatalf("expected fallback candidate count 3, got %d", len(candidateList))
	}
	if candidateList[0] != "测试" {
		t.Fatalf("expected fallback candidate 测试, got %#v", candidateList[0])
	}

	_, selectResp := sendProtocolMessage(t, server, "client-4", map[string]interface{}{
		"method":  "filterKeyDown",
		"seqNum":  4,
		"keyCode": 0x31,
	})
	if selectResp["commitString"] != "测试" {
		t.Fatalf("expected number key to commit first fallback candidate, got %#v", selectResp)
	}
	if selectResp["return"] != float64(1) {
		t.Fatalf("expected candidate selection return 1, got %#v", selectResp)
	}
	if selectResp["showCandidates"] != false {
		t.Fatalf("expected candidate window to close, got %#v", selectResp)
	}
}

func TestServerHandleMessageSimplePinyinExactCandidateCommitFlow(t *testing.T) {
	server := newTestServerWithSimplePinyin()

	sendProtocolMessage(t, server, "client-5", map[string]interface{}{
		"method":          "init",
		"seqNum":          1,
		"id":              testSimplePinyinGUID,
		"isWindows8Above": true,
		"isMetroApp":      false,
		"isUiLess":        false,
		"isConsole":       false,
	})

	for i, key := range []struct {
		keyCode  int
		charCode rune
	}{
		{keyCode: 0x4E, charCode: 'n'},
		{keyCode: 0x49, charCode: 'i'},
		{keyCode: 0x48, charCode: 'h'},
		{keyCode: 0x41, charCode: 'a'},
		{keyCode: 0x4F, charCode: 'o'},
	} {
		sendProtocolMessage(t, server, "client-5", map[string]interface{}{
			"method":   "filterKeyDown",
			"seqNum":   i + 2,
			"keyCode":  key.keyCode,
			"charCode": key.charCode,
		})
	}

	_, commitResp := sendProtocolMessage(t, server, "client-5", map[string]interface{}{
		"method":  "filterKeyDown",
		"seqNum":  7,
		"keyCode": 0x0D,
	})
	if commitResp["commitString"] != "你好" {
		t.Fatalf("expected enter to commit exact first candidate 你好, got %#v", commitResp)
	}
	if commitResp["return"] != float64(1) {
		t.Fatalf("expected enter commit return 1, got %#v", commitResp)
	}
}

func TestServerHandleMessageRimeRequestResponseFlow(t *testing.T) {
	server := newTestServerWithRime()

	sendProtocolMessage(t, server, "client-6", map[string]interface{}{
		"method":          "init",
		"seqNum":          1,
		"id":              testRimeGUID,
		"isWindows8Above": true,
		"isMetroApp":      false,
		"isUiLess":        false,
		"isConsole":       false,
	})

	service, ok := server.clients["client-6"].Service.(*rimeime.IME)
	if !ok {
		t.Fatal("expected concrete Rime IME service")
	}
	if !service.BackendAvailable() {
		t.Skip("native Rime backend unavailable in test environment")
	}

	_, firstResp := sendProtocolMessage(t, server, "client-6", map[string]interface{}{
		"method":   "filterKeyDown",
		"seqNum":   2,
		"keyCode":  0x4E,
		"charCode": 'n',
	})
	if firstResp["return"] != float64(1) {
		t.Fatalf("expected first key return 1, got %#v", firstResp)
	}

	_, firstKeyState := sendProtocolMessage(t, server, "client-6", map[string]interface{}{
		"method":   "onKeyDown",
		"seqNum":   3,
		"keyCode":  0x4E,
		"charCode": 'n',
	})
	if firstKeyState["compositionString"] != "n" {
		t.Fatalf("expected onKeyDown to expose n, got %#v", firstKeyState)
	}
	candidateList, ok := firstKeyState["candidateList"].([]interface{})
	if !ok || len(candidateList) == 0 {
		t.Fatalf("expected prefix candidates, got %#v", firstKeyState["candidateList"])
	}
	if candidateList[0] != "你" {
		t.Fatalf("expected first candidate 你, got %#v", candidateList[0])
	}

	_, secondResp := sendProtocolMessage(t, server, "client-6", map[string]interface{}{
		"method":   "filterKeyDown",
		"seqNum":   4,
		"keyCode":  0x49,
		"charCode": 'i',
	})
	if secondResp["return"] != float64(1) {
		t.Fatalf("expected second key return 1, got %#v", secondResp)
	}

	_, secondKeyState := sendProtocolMessage(t, server, "client-6", map[string]interface{}{
		"method":   "onKeyDown",
		"seqNum":   5,
		"keyCode":  0x49,
		"charCode": 'i',
	})
	if secondKeyState["compositionString"] != "ni" {
		t.Fatalf("expected second key to build ni, got %#v", secondKeyState)
	}
	secondCandidates, ok := secondKeyState["candidateList"].([]interface{})
	if !ok || len(secondCandidates) == 0 {
		t.Fatalf("expected exact candidates after ni, got %#v", secondKeyState["candidateList"])
	}
	if secondCandidates[1] != "呢" {
		t.Fatalf("expected second candidate 呢, got %#v", secondCandidates[1])
	}

	_, selectFilterResp := sendProtocolMessage(t, server, "client-6", map[string]interface{}{
		"method":  "filterKeyDown",
		"seqNum":  6,
		"keyCode": 0x32,
	})
	if selectFilterResp["return"] != float64(1) {
		t.Fatalf("expected number filter to be handled, got %#v", selectFilterResp)
	}

	_, selectResp := sendProtocolMessage(t, server, "client-6", map[string]interface{}{
		"method":  "onKeyDown",
		"seqNum":  7,
		"keyCode": 0x32,
	})
	if selectResp["commitString"] != "呢" {
		t.Fatalf("expected number key to commit 呢, got %#v", selectResp)
	}
	if selectResp["return"] != float64(1) {
		t.Fatalf("expected candidate selection return 1, got %#v", selectResp)
	}
}

func TestServerHandleMessageFcitx5RequestResponseFlow(t *testing.T) {
	server := newTestServerWithFcitx5()

	sendProtocolMessage(t, server, "client-7", map[string]interface{}{
		"method":          "init",
		"seqNum":          1,
		"id":              testFcitx5GUID,
		"isWindows8Above": true,
		"isMetroApp":      false,
		"isUiLess":        false,
		"isConsole":       false,
	})

	_, firstResp := sendProtocolMessage(t, server, "client-7", map[string]interface{}{
		"method":   "filterKeyDown",
		"seqNum":   2,
		"keyCode":  0x48,
		"charCode": 'h',
	})
	if firstResp["compositionString"] != "ha" {
		t.Fatalf("expected first key to build ha, got %#v", firstResp)
	}
	if firstResp["return"] != float64(1) {
		t.Fatalf("expected first key return 1, got %#v", firstResp)
	}
	candidateList, ok := firstResp["candidateList"].([]interface{})
	if !ok {
		t.Fatalf("expected candidate list array, got %#v", firstResp["candidateList"])
	}
	if len(candidateList) != 5 {
		t.Fatalf("expected 5 candidates, got %d", len(candidateList))
	}
	if candidateList[2] != "喝" {
		t.Fatalf("expected third candidate 喝, got %#v", candidateList[2])
	}

	_, selectResp := sendProtocolMessage(t, server, "client-7", map[string]interface{}{
		"method":        "onKeyDown",
		"seqNum":        3,
		"keyCode":       0x33,
		"candidateList": []string{"哈", "呵", "喝", "和", "河"},
	})
	if selectResp["commitString"] != "喝" {
		t.Fatalf("expected number key to commit 喝, got %#v", selectResp)
	}
	if selectResp["return"] != float64(1) {
		t.Fatalf("expected candidate selection return 1, got %#v", selectResp)
	}
}
