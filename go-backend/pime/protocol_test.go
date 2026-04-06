package pime

import (
	"encoding/json"
	"testing"
)

func TestResponseJSONIncludesClearedCompositionState(t *testing.T) {
	resp := NewResponse(1, true)
	resp.ReturnValue = 1

	payload, err := resp.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON failed: %v", err)
	}

	var decoded map[string]interface{}
	if err := json.Unmarshal(payload, &decoded); err != nil {
		t.Fatalf("unmarshal response failed: %v", err)
	}

	if value, ok := decoded["compositionString"]; !ok || value != "" {
		t.Fatalf("expected empty compositionString to be serialized, got %#v", decoded["compositionString"])
	}
	if value, ok := decoded["showCandidates"]; !ok || value.(bool) {
		t.Fatalf("expected showCandidates=false to be serialized, got %#v", decoded["showCandidates"])
	}
	if value, ok := decoded["candidateList"]; !ok {
		t.Fatalf("expected candidateList to be serialized, got %#v", decoded)
	} else if list, ok := value.([]interface{}); !ok || len(list) != 0 {
		t.Fatalf("expected empty candidateList, got %#v", value)
	}
}

func TestParseRequestAcceptsNumericKeyStates(t *testing.T) {
	req, err := ParseRequest([]byte(`{
		"method": "onKeyDown",
		"seqNum": 1,
		"keyStates": [0, 1, 0, 2]
	}`))
	if err != nil {
		t.Fatalf("ParseRequest returned error: %v", err)
	}

	want := []int{0, 1, 0, 2}
	if len(req.KeyStates) != len(want) {
		t.Fatalf("expected %d key states, got %d", len(want), len(req.KeyStates))
	}
	for i, expected := range want {
		if req.KeyStates[i] != expected {
			t.Fatalf("expected keyStates[%d]=%d, got %d", i, expected, req.KeyStates[i])
		}
	}
}

func TestParseRequestAcceptsBooleanKeyStates(t *testing.T) {
	req, err := ParseRequest([]byte(`{
		"method": "onKeyDown",
		"seqNum": 1,
		"keyStates": [true, false, true]
	}`))
	if err != nil {
		t.Fatalf("ParseRequest returned error: %v", err)
	}

	want := []int{1, 0, 1}
	if len(req.KeyStates) != len(want) {
		t.Fatalf("expected %d key states, got %d", len(want), len(req.KeyStates))
	}
	for i, expected := range want {
		if req.KeyStates[i] != expected {
			t.Fatalf("expected keyStates[%d]=%d, got %d", i, expected, req.KeyStates[i])
		}
	}
}

func TestParseRequestAcceptsStringAndNumericID(t *testing.T) {
	stringReq, err := ParseRequest([]byte(`{"method":"init","seqNum":1,"id":"{guid}"}`))
	if err != nil {
		t.Fatalf("ParseRequest returned error for string id: %v", err)
	}
	if got := stringReq.ID.StringValue(); got != "{guid}" {
		t.Fatalf("expected string id {guid}, got %q", got)
	}

	numericReq, err := ParseRequest([]byte(`{"method":"onCommand","seqNum":2,"id":3}`))
	if err != nil {
		t.Fatalf("ParseRequest returned error for numeric id: %v", err)
	}
	if got := numericReq.ID.IntValue(); got != 3 {
		t.Fatalf("expected numeric id 3, got %d", got)
	}
}
