// 喵喵输入法 Go 实现
// 每个输入法是一个独立的包
package meow

import (
	"log"
	"unicode/utf8"

	"github.com/EasyIME/pime-go/pime"
)

// IME 喵喵输入法结构
type IME struct {
	*pime.TextServiceBase
	compositionString string
	showCandidates    bool
	candidateCursor   int
	asciiMode         bool
}

// 候选词列表
var candidates = []string{"喵", "描", "秒", "妙"}

const (
	modeIconCommandID = 3000
	langIconCommandID = 3001
)

func normalizeLetterCharCode(keyCode, charCode int) int {
	if charCode != 0 {
		return charCode
	}
	if keyCode >= 0x41 && keyCode <= 0x5A {
		return keyCode + 32
	}
	return charCode
}

func isModifierKey(keyCode int) bool {
	switch keyCode {
	case 0x10, // VK_SHIFT
		0x11, // VK_CONTROL
		0x12: // VK_MENU / Alt
		return true
	default:
		return false
	}
}

func isPrintableKey(keyCode, charCode int) bool {
	if charCode >= 0x20 {
		return true
	}
	return keyCode >= 0x30 && keyCode <= 0x5A
}

func trimLastRune(s string) string {
	if s == "" {
		return s
	}
	_, size := utf8.DecodeLastRuneInString(s)
	return s[:len(s)-size]
}

// New 创建喵喵输入法实例
func New(client *pime.Client) pime.TextService {
	return &IME{
		TextServiceBase:   pime.NewTextServiceBase(client),
		compositionString: "",
		showCandidates:    false,
		candidateCursor:   0,
	}
}

// HandleRequest 处理请求
func (ime *IME) HandleRequest(req *pime.Request) *pime.Response {
	resp := pime.NewResponse(req.SeqNum, true)

	switch req.Method {
	case "onActivate":
		log.Println("喵喵输入法已激活")
		pime.AddLangButtons(resp, ime.Client, ime.asciiMode, modeIconCommandID, langIconCommandID)
		resp.ReturnValue = 1

	case "onDeactivate":
		log.Println("喵喵输入法已失活")
		pime.RemoveLangButtons(resp, ime.Client)
		resp.ReturnValue = 1

	case "filterKeyDown":
		return ime.filterKeyDown(req, resp)

	case "onKeyDown":
		return ime.onKeyDown(req, resp)

	case "filterKeyUp":
		resp.ReturnValue = 0

	case "onCompositionTerminated":
		// 清理状态
		ime.compositionString = ""
		ime.showCandidates = false
		ime.candidateCursor = 0

	case "onCommand":
		return ime.onCommand(req, resp)
	}

	return resp
}

// filterKeyDown 过滤按键
func (ime *IME) filterKeyDown(req *pime.Request, resp *pime.Response) *pime.Response {
	keyCode := req.KeyCode
	charCode := normalizeLetterCharCode(keyCode, req.CharCode)

	if isModifierKey(keyCode) {
		resp.ReturnValue = 0
		return resp
	}

	if ime.asciiMode && ime.compositionString == "" && !ime.showCandidates && isPrintableKey(keyCode, charCode) {
		resp.ReturnValue = 0
		return resp
	}

	if ime.showCandidates {
		switch keyCode {
		case 0x26, // VK_UP
			0x1B: // VK_ESCAPE
			resp.ReturnValue = 1
			return resp
		}
		if keyCode >= 0x31 && keyCode <= 0x34 {
			resp.ReturnValue = 1
			return resp
		}
	}

	// 如果组合字符串为空，不处理某些按键
	if ime.compositionString == "" {
		switch keyCode {
		case 0x0D, // VK_RETURN
			0x08, // VK_BACK
			0x25, // VK_LEFT
			0x26, // VK_UP
			0x27, // VK_DOWN
			0x28: // VK_RIGHT
			resp.ReturnValue = 0 // 不处理
			return resp
		}
	}

	if ime.compositionString != "" {
		switch keyCode {
		case 0x0D, // VK_RETURN
			0x08, // VK_BACK
			0x1B, // VK_ESCAPE
			0x25, // VK_LEFT
			0x27, // VK_RIGHT
			0x28: // VK_DOWN
			resp.ReturnValue = 1
			return resp
		}
	}

	if isPrintableKey(keyCode, charCode) {
		resp.ReturnValue = 1
		return resp
	}

	resp.ReturnValue = 1 // 处理
	return resp
}

// onKeyDown 处理按键
func (ime *IME) onKeyDown(req *pime.Request, resp *pime.Response) *pime.Response {
	keyCode := req.KeyCode
	charCode := normalizeLetterCharCode(keyCode, req.CharCode)

	if ime.asciiMode && ime.compositionString == "" && !ime.showCandidates && isPrintableKey(keyCode, charCode) {
		resp.ReturnValue = 0
		return resp
	}

	if isModifierKey(keyCode) {
		resp.ReturnValue = 0
		return resp
	}

	if ime.showCandidates {
		switch keyCode {
		case 0x26, // VK_UP
			0x1B: // VK_ESCAPE
			ime.showCandidates = false
			resp.ShowCandidates = false
			resp.CompositionString = ime.compositionString
			resp.ReturnValue = 1
			return resp
		}
	}

	// 处理 'm' 键 (109 或 77)
	if charCode == 109 || charCode == 77 {
		// 添加 '喵' 到组合字符串
		if ime.compositionString == "" {
			// 第一次按 'm'
			ime.compositionString = "喵"
			resp.CompositionString = ime.compositionString
			resp.ReturnValue = 1
		} else {
			// 重复按 'm'，显示候选词
			ime.showCandidates = true
			resp.CompositionString = ime.compositionString
			resp.CandidateList = candidates
			resp.ShowCandidates = true
			resp.ReturnValue = 1
		}
		return resp
	}

	if keyCode == 0x28 && ime.compositionString != "" { // VK_DOWN
		ime.showCandidates = true
		resp.CompositionString = ime.compositionString
		resp.CandidateList = candidates
		resp.ShowCandidates = true
		resp.ReturnValue = 1
		return resp
	}

	// 处理数字键选择候选词
	if keyCode >= 0x31 && keyCode <= 0x34 { // '1' - '4'
		if ime.showCandidates {
			index := int(keyCode - 0x31)
			if index < len(candidates) {
				// 提交选中的候选词
				resp.CommitString = candidates[index]
				// 重置状态
				ime.compositionString = ""
				ime.showCandidates = false
				resp.CompositionString = ""
				resp.ShowCandidates = false
				resp.ReturnValue = 1
				return resp
			}
		}
	}

	// 处理回车键 - 提交
	if keyCode == 0x0D { // VK_RETURN
		if ime.compositionString != "" {
			resp.CommitString = ime.compositionString
			// 重置状态
			ime.compositionString = ""
			ime.showCandidates = false
			resp.CompositionString = ""
			resp.ShowCandidates = false
			resp.ReturnValue = 1
			return resp
		}
	}

	// 处理退格键
	if keyCode == 0x08 { // VK_BACK
		if ime.compositionString != "" {
			// 删除最后一个字符，让测试输入更接近 Python 版本。
			ime.compositionString = trimLastRune(ime.compositionString)
			ime.showCandidates = false
			resp.CompositionString = ime.compositionString
			resp.ShowCandidates = false
			resp.ReturnValue = 1
			return resp
		}
	}

	// 处理 Escape 键
	if keyCode == 0x1B { // VK_ESCAPE
		if ime.compositionString != "" {
			// 取消输入
			ime.compositionString = ""
			ime.showCandidates = false
			resp.CompositionString = ""
			resp.ShowCandidates = false
			resp.ReturnValue = 1
			return resp
		}
	}

	if isPrintableKey(keyCode, charCode) {
		ime.compositionString += "喵"
		ime.showCandidates = false
		resp.CompositionString = ime.compositionString
		resp.ShowCandidates = false
		resp.ReturnValue = 1
		return resp
	}

	// 其他按键不处理
	resp.ReturnValue = 0
	return resp
}

func (ime *IME) onCommand(req *pime.Request, resp *pime.Response) *pime.Response {
	commandID, ok := req.Data["commandId"].(float64)
	if !ok {
		resp.ReturnValue = 0
		return resp
	}

	switch int(commandID) {
	case modeIconCommandID, langIconCommandID:
		ime.asciiMode = !ime.asciiMode
		pime.ChangeLangButtons(resp, ime.Client, ime.asciiMode)
		resp.ReturnValue = 1
	default:
		resp.ReturnValue = 0
	}
	return resp
}

// Init 初始化
func (ime *IME) Init(req *pime.Request) bool {
	return true
}

// Close 关闭
func (ime *IME) Close() {
	// 清理资源
}
