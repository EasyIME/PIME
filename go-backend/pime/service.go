// PIME 文本服务接口和基础实现
package pime

// TextServiceBase 文本服务基础实现
type TextServiceBase struct {
	Client        *Client
	Composition   string
	CandidateList []string
	CursorPos     int
}

// NewTextServiceBase 创建基础文本服务
func NewTextServiceBase(client *Client) *TextServiceBase {
	return &TextServiceBase{
		Client:        client,
		Composition:   "",
		CandidateList: make([]string, 0),
		CursorPos:     0,
	}
}

// Init 初始化服务
func (s *TextServiceBase) Init(req *Request) bool {
	return true
}

// HandleRequest 处理请求
func (s *TextServiceBase) HandleRequest(req *Request) *Response {
	resp := NewResponse(req.SeqNum, true)

	switch req.Method {
	case "onActivate":
		s.onActivate(req, resp)
	case "onDeactivate":
		s.onDeactivate(req, resp)
	case "filterKeyDown":
		s.filterKeyDown(req, resp)
	case "filterKeyUp":
		s.filterKeyUp(req, resp)
	case "onCompositionTerminated":
		s.onCompositionTerminated(req, resp)
	case "onCommand":
		s.onCommand(req, resp)
	case "onMenu":
		s.onMenu(req, resp)
	}

	return resp
}

// Close 关闭服务
func (s *TextServiceBase) Close() {
	// 清理资源
}

// 事件处理方法（可被子类覆盖）

func (s *TextServiceBase) onActivate(req *Request, resp *Response) {
	// 输入法激活时的处理
}

func (s *TextServiceBase) onDeactivate(req *Request, resp *Response) {
	// 输入法失活时的处理
}

func (s *TextServiceBase) filterKeyDown(req *Request, resp *Response) {
	// 按键按下处理
	// 返回 returnValue: 0=不处理, 1=已处理
	resp.ReturnValue = 0
}

func (s *TextServiceBase) filterKeyUp(req *Request, resp *Response) {
	// 按键释放处理
	resp.ReturnValue = 0
}

func (s *TextServiceBase) onCompositionTerminated(req *Request, resp *Response) {
	// 组合终止处理
}

func (s *TextServiceBase) onCommand(req *Request, resp *Response) {
	// 命令处理
}

func (s *TextServiceBase) onMenu(req *Request, resp *Response) {
	// 菜单请求，默认无菜单
	resp.ReturnData = nil
}

// Helper 方法

// UpdateComposition 更新组合字符串
func (s *TextServiceBase) UpdateComposition(resp *Response, composition string, cursorPos int) {
	resp.CompositionString = composition
	resp.CursorPos = cursorPos
}

// SetCandidates 设置候选词列表
func (s *TextServiceBase) SetCandidates(resp *Response, candidates []string, show bool) {
	resp.CandidateList = candidates
	resp.ShowCandidates = show
}

// CommitString 提交字符串
func (s *TextServiceBase) CommitString(resp *Response, text string) {
	resp.CommitString = text
}
