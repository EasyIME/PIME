// PIME 通信协议定义
package pime

import (
	"encoding/json"
	"fmt"
)

// 消息类型
const (
	MsgPIME = "PIME_MSG"
)

type FlexibleID struct {
	String string
	Int    int
	IsInt  bool
}

type KeyStates []int

func (k *KeyStates) UnmarshalJSON(data []byte) error {
	var bools []bool
	if err := json.Unmarshal(data, &bools); err == nil {
		states := make(KeyStates, len(bools))
		for i, v := range bools {
			if v {
				states[i] = 1
			}
		}
		*k = states
		return nil
	}

	var ints []int
	if err := json.Unmarshal(data, &ints); err == nil {
		states := make(KeyStates, len(ints))
		copy(states, ints)
		*k = states
		return nil
	}

	return fmt.Errorf("invalid keyStates payload: %s", string(data))
}

func (k KeyStates) IsKeyDown(code int) bool {
	return code >= 0 && code < len(k) && (k[code]&(1<<7)) != 0
}

func (k KeyStates) IsKeyToggled(code int) bool {
	return code >= 0 && code < len(k) && (k[code]&1) != 0
}

func (id FlexibleID) StringValue() string {
	if id.IsInt {
		return ""
	}
	return id.String
}

func (id FlexibleID) IntValue() int {
	if id.IsInt {
		return id.Int
	}
	return 0
}

// Request PIME请求结构
type Request struct {
	Method            string     `json:"method"`
	SeqNum            int        `json:"seqNum"`
	ID                FlexibleID `json:"-"`
	IsWindows8Above   bool       `json:"isWindows8Above,omitempty"`
	IsMetroApp        bool       `json:"isMetroApp,omitempty"`
	IsUiLess          bool       `json:"isUiLess,omitempty"`
	IsConsole         bool       `json:"isConsole,omitempty"`
	IsKeyboardOpen    bool       `json:"isKeyboardOpen,omitempty"`
	Opened            bool       `json:"opened,omitempty"`
	Forced            bool       `json:"forced,omitempty"`
	CommandType       int        `json:"type,omitempty"`
	CharCode          int        `json:"charCode,omitempty"`
	KeyCode           int        `json:"keyCode,omitempty"`
	RepeatCount       int        `json:"repeatCount,omitempty"`
	ScanCode          int        `json:"scanCode,omitempty"`
	IsExtended        bool       `json:"isExtended,omitempty"`
	KeyStates         KeyStates  `json:"keyStates,omitempty"`
	CompositionString string     `json:"compositionString,omitempty"`
	CandidateList     []string   `json:"candidateList,omitempty"`
	ShowCandidates    bool       `json:"showCandidates,omitempty"`
	CursorPos         int        `json:"cursorPos,omitempty"`
	SelStart          int        `json:"selStart,omitempty"`
	SelEnd            int        `json:"selEnd,omitempty"`
	// 扩展字段
	Data map[string]interface{} `json:"data,omitempty"`
}

func (r *Request) UnmarshalJSON(data []byte) error {
	type Alias Request
	aux := &struct {
		ID json.RawMessage `json:"id,omitempty"`
		*Alias
	}{
		Alias: (*Alias)(r),
	}
	if err := json.Unmarshal(data, aux); err != nil {
		return err
	}
	if len(aux.ID) == 0 {
		return nil
	}

	var s string
	if err := json.Unmarshal(aux.ID, &s); err == nil {
		r.ID = FlexibleID{String: s}
		return nil
	}

	var n int
	if err := json.Unmarshal(aux.ID, &n); err == nil {
		r.ID = FlexibleID{Int: n, IsInt: true}
		return nil
	}

	return fmt.Errorf("invalid id payload: %s", string(aux.ID))
}

// ButtonInfo 按钮信息
type ButtonInfo struct {
	ID        string `json:"id"`
	Icon      string `json:"icon,omitempty"`
	Text      string `json:"text,omitempty"`
	Tooltip   string `json:"tooltip,omitempty"`
	CommandID int    `json:"commandId,omitempty"`
	Type      string `json:"type,omitempty"` // "button", "toggle", "menu"
	Enable    bool   `json:"enable,omitempty"`
	Toggled   bool   `json:"toggled,omitempty"`
}

// Response PIME响应结构
type Response struct {
	SeqNum            int                    `json:"seqNum"`
	Success           bool                   `json:"success"`
	ReturnValue       int                    `json:"returnValue,omitempty"`
	ReturnData        interface{}            `json:"-"`
	CompositionString string                 `json:"compositionString"`
	CommitString      string                 `json:"commitString,omitempty"`
	CandidateList     []string               `json:"candidateList"`
	ShowCandidates    bool                   `json:"showCandidates"`
	CursorPos         int                    `json:"cursorPos"`
	CompositionCursor int                    `json:"compositionCursor"`
	CandidateCursor   int                    `json:"candidateCursor"`
	SelStart          int                    `json:"selStart"`
	SelEnd            int                    `json:"selEnd"`
	SetSelKeys        string                 `json:"setSelKeys,omitempty"`
	Message           string                 `json:"message,omitempty"`
	CustomizeUI       map[string]interface{} `json:"customizeUI,omitempty"`
	// 按钮相关
	AddButton    []ButtonInfo `json:"addButton,omitempty"`
	RemoveButton []string     `json:"removeButton,omitempty"`
	ChangeButton []ButtonInfo `json:"changeButton,omitempty"`
}

// ParseRequest 解析请求消息
func ParseRequest(data []byte) (*Request, error) {
	var req Request
	if err := json.Unmarshal(data, &req); err != nil {
		return nil, fmt.Errorf("unmarshal request failed: %w", err)
	}
	return &req, nil
}

// ToJSON 转换为 JSON 字节
func (r *Response) ToJSON() ([]byte, error) {
	return json.Marshal(r)
}

// NewResponse 创建新响应
func NewResponse(seqNum int, success bool) *Response {
	return &Response{
		SeqNum:            seqNum,
		Success:           success,
		CandidateList:     []string{},
		CompositionString: "",
	}
}
