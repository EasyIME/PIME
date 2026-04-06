package main

import (
	"testing"

	"github.com/EasyIME/pime-go/pime"
)

func TestConvertResponseIncludesClearedCompositionState(t *testing.T) {
	server := NewServer()
	resp := pime.NewResponse(1, true)
	resp.ReturnValue = 1

	got := server.convertResponse(resp)

	if value, ok := got["compositionString"]; !ok || value != "" {
		t.Fatalf("expected empty compositionString, got %#v", got["compositionString"])
	}
	if value, ok := got["candidateList"]; !ok {
		t.Fatalf("expected candidateList in response, got %#v", got)
	} else if list, ok := value.([]string); !ok || len(list) != 0 {
		t.Fatalf("expected empty candidateList, got %#v", value)
	}
	if value, ok := got["showCandidates"]; !ok || value.(bool) {
		t.Fatalf("expected showCandidates=false, got %#v", got["showCandidates"])
	}
	if value, ok := got["selStart"]; !ok || value.(int) != 0 {
		t.Fatalf("expected selStart=0, got %#v", got["selStart"])
	}
	if value, ok := got["selEnd"]; !ok || value.(int) != 0 {
		t.Fatalf("expected selEnd=0, got %#v", got["selEnd"])
	}
}

func TestConvertResponseUsesReturnDataWhenPresent(t *testing.T) {
	server := NewServer()
	resp := pime.NewResponse(2, true)
	resp.ReturnValue = 1
	resp.ReturnData = []map[string]interface{}{
		{"id": 1, "text": "中文 → 西文"},
	}

	got := server.convertResponse(resp)

	items, ok := got["return"].([]map[string]interface{})
	if !ok || len(items) != 1 {
		t.Fatalf("expected menu return data, got %#v", got["return"])
	}
}
