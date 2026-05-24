// PIME Go 后端主入口
// 参考 python/server.py 实现
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"github.com/EasyIME/pime-go/pime"

	// 导入输入法包
	"github.com/EasyIME/pime-go/input_methods/fcitx5"
	"github.com/EasyIME/pime-go/input_methods/meow"
	"github.com/EasyIME/pime-go/input_methods/rime"
	simplepinyin "github.com/EasyIME/pime-go/input_methods/simple_pinyin"
)

// Client 客户端连接
type Client struct {
	ID              string
	GUID            string
	IsWindows8Above bool
	IsMetroApp      bool
	IsUiLess        bool
	IsConsole       bool
	Service         pime.TextService
}

// ServiceFactory 服务工厂函数
type ServiceFactory func(client *pime.Client, guid string) pime.TextService

// Server PIME 服务器
type Server struct {
	mu        sync.RWMutex
	clients   map[string]*Client
	factories map[string]ServiceFactory // guid -> factory
	reader    *bufio.Reader
	running   bool
}

func stringifyData(data map[string]interface{}) string {
	if len(data) == 0 {
		return ""
	}
	raw, err := json.Marshal(data)
	if err != nil {
		return fmt.Sprintf("<marshal error: %v>", err)
	}
	return string(raw)
}

func logRequestSummary(clientID string, req *pime.Request) {
	log.Printf(
		"收到请求 client=%s method=%s seq=%d id=%q commandId=%d keyCode=%d charCode=%d repeat=%d scan=%d composing=%q candidates=%d showCandidates=%t cursor=%d data=%s",
		clientID,
		req.Method,
		req.SeqNum,
		req.ID.StringValue(),
		req.ID.IntValue(),
		req.KeyCode,
		req.CharCode,
		req.RepeatCount,
		req.ScanCode,
		req.CompositionString,
		len(req.CandidateList),
		req.ShowCandidates,
		req.CursorPos,
		stringifyData(req.Data),
	)
}

func logResponseSummary(clientID string, resp map[string]interface{}) {
	raw, err := json.Marshal(resp)
	if err != nil {
		log.Printf("发送响应 client=%s marshal_error=%v", clientID, err)
		return
	}
	log.Printf("发送响应 client=%s payload=%s", clientID, string(raw))
}

// NewServer 创建服务器
func NewServer() *Server {
	return &Server{
		clients:   make(map[string]*Client),
		factories: make(map[string]ServiceFactory),
		reader:    bufio.NewReader(os.Stdin),
	}
}

// RegisterService 注册输入法服务工厂
func (s *Server) RegisterService(guid string, factory ServiceFactory) {
	s.mu.Lock()
	defer s.mu.Unlock()
	guid = strings.ToLower(guid)
	s.factories[guid] = factory
	log.Printf("注册输入法服务: %s", guid)
}

// Run 运行服务器
func (s *Server) Run() error {
	s.running = true
	log.Println("PIME Go 后端服务器已启动")

	for s.running {
		line, err := s.reader.ReadString('\n')
		if err != nil {
			if err.Error() == "EOF" {
				log.Println("收到 EOF，服务器停止")
				return nil
			}
			return fmt.Errorf("读取错误: %w", err)
		}

		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		if err := s.handleMessage(line); err != nil {
			log.Printf("处理消息错误: %v", err)
			// 发送错误响应，防止客户端阻塞
			parts := strings.SplitN(line, "|", 2)
			if len(parts) == 2 {
				s.sendResponse(parts[0], map[string]interface{}{
					"success": false,
					"error":   err.Error(),
				})
			}
		}
	}

	return nil
}

// handleMessage 处理消息
// 格式: "<client_id>|<JSON>"
func (s *Server) handleMessage(line string) error {
	parts := strings.SplitN(line, "|", 2)
	if len(parts) != 2 {
		return fmt.Errorf("无效的消息格式")
	}

	clientID := parts[0]
	jsonData := parts[1]

	var req pime.Request
	if err := json.Unmarshal([]byte(jsonData), &req); err != nil {
		return fmt.Errorf("解析 JSON 失败: %w", err)
	}

	logRequestSummary(clientID, &req)

	// 处理请求
	resp := s.handleRequest(clientID, &req)

	// 发送响应
	return s.sendResponse(clientID, resp)
}

// handleRequest 处理请求
func (s *Server) handleRequest(clientID string, req *pime.Request) map[string]interface{} {
	s.mu.Lock()
	defer s.mu.Unlock()

	switch req.Method {
	case "init":
		// PIME 在 init 时通过顶层 id 传递语言配置 GUID。
		// 为了兼容已有调用，也接受 data.guid。
		guid := req.ID.StringValue()
		if guid == "" && req.Data != nil {
			guid, _ = req.Data["guid"].(string)
		}
		guid = strings.ToLower(guid)
		if guid == "" {
			log.Printf("初始化失败 client=%s seq=%d 原因=缺少guid id=%q data=%s", clientID, req.SeqNum, req.ID.StringValue(), stringifyData(req.Data))
			return map[string]interface{}{
				"seqNum":  req.SeqNum,
				"success": false,
				"error":   "缺少 guid",
			}
		}

		// 创建客户端
		client := &Client{
			ID:              clientID,
			GUID:            guid,
			IsWindows8Above: req.IsWindows8Above,
			IsMetroApp:      req.IsMetroApp,
			IsUiLess:        req.IsUiLess,
			IsConsole:       req.IsConsole,
		}

		// 获取输入法服务工厂
		factory, ok := s.factories[guid]
		if !ok {
			log.Printf("初始化失败 client=%s seq=%d 原因=未知输入法 guid=%s", clientID, req.SeqNum, guid)
			return map[string]interface{}{
				"seqNum":  req.SeqNum,
				"success": false,
				"error":   fmt.Sprintf("未知的输入法: %s", guid),
			}
		}

		// 创建输入法服务
		pimeClient := &pime.Client{
			ID:              clientID,
			GUID:            guid,
			IsWindows8Above: req.IsWindows8Above,
			IsMetroApp:      req.IsMetroApp,
			IsUiLess:        req.IsUiLess,
			IsConsole:       req.IsConsole,
		}
		client.Service = factory(pimeClient, guid)
		s.clients[clientID] = client

		// 初始化服务
		if !client.Service.Init(req) {
			delete(s.clients, clientID)
			log.Printf("初始化失败 client=%s seq=%d guid=%s 原因=Service.Init返回false", clientID, req.SeqNum, guid)
			return map[string]interface{}{
				"seqNum":  req.SeqNum,
				"success": false,
				"error":   "初始化失败",
			}
		}

		log.Printf("初始化成功 client=%s seq=%d guid=%s windows8=%t metro=%t uiless=%t console=%t", clientID, req.SeqNum, guid, req.IsWindows8Above, req.IsMetroApp, req.IsUiLess, req.IsConsole)

		return map[string]interface{}{
			"seqNum":  req.SeqNum,
			"success": true,
		}

	case "close":
		if client, ok := s.clients[clientID]; ok {
			client.Service.Close()
			delete(s.clients, clientID)
			log.Printf("客户端关闭 client=%s guid=%s", clientID, client.GUID)
		} else {
			log.Printf("客户端关闭 client=%s 但未找到已初始化会话", clientID)
		}
		return map[string]interface{}{
			"seqNum":  req.SeqNum,
			"success": true,
		}

	case "onActivate", "onDeactivate", "filterKeyDown", "onKeyDown",
		"filterKeyUp", "onKeyUp", "onCommand", "onMenu", "onCompositionTerminated",
		"onPreservedKey", "onLangProfileActivated":
		// 转发到输入法服务
		client, ok := s.clients[clientID]
		if !ok {
			log.Printf("请求失败 client=%s seq=%d method=%s 原因=客户端未初始化", clientID, req.SeqNum, req.Method)
			return map[string]interface{}{
				"seqNum":  req.SeqNum,
				"success": false,
				"error":   "客户端未初始化",
			}
		}

		log.Printf("转发请求 client=%s seq=%d method=%s guid=%s", clientID, req.SeqNum, req.Method, client.GUID)
		resp := client.Service.HandleRequest(req)
		return s.convertResponse(resp)

	default:
		log.Printf("请求失败 client=%s seq=%d method=%s 原因=未知方法", clientID, req.SeqNum, req.Method)
		return map[string]interface{}{
			"seqNum":  req.SeqNum,
			"success": false,
			"error":   fmt.Sprintf("未知的方法: %s", req.Method),
		}
	}
}

// sendResponse 发送响应
func (s *Server) sendResponse(clientID string, resp map[string]interface{}) error {
	logResponseSummary(clientID, resp)
	data, err := json.Marshal(resp)
	if err != nil {
		return fmt.Errorf("序列化响应失败: %w", err)
	}

	fmt.Printf("%s|%s|%s\n", pime.MsgPIME, clientID, string(data))
	return nil
}

// convertResponse 转换响应格式
func (s *Server) convertResponse(resp *pime.Response) map[string]interface{} {
	candidateList := resp.CandidateList
	if candidateList == nil {
		candidateList = []string{}
	}
	m := map[string]interface{}{
		"success":           resp.Success,
		"seqNum":            resp.SeqNum,
		"cursorPos":         resp.CursorPos,
		"compositionCursor": resp.CompositionCursor,
		"candidateCursor":   resp.CandidateCursor,
		"showCandidates":    resp.ShowCandidates,
		"compositionString": resp.CompositionString,
		"candidateList":     candidateList,
		"selStart":          resp.SelStart,
		"selEnd":            resp.SelEnd,
	}
	if resp.ReturnData != nil {
		m["return"] = resp.ReturnData
	} else {
		m["return"] = resp.ReturnValue
	}

	if resp.CommitString != "" {
		m["commitString"] = resp.CommitString
	}
	if resp.SetSelKeys != "" {
		m["setSelKeys"] = resp.SetSelKeys
	}
	if len(resp.CustomizeUI) > 0 {
		m["customizeUI"] = resp.CustomizeUI
	}
	if len(resp.AddButton) > 0 {
		m["addButton"] = resp.AddButton
	}
	if len(resp.RemoveButton) > 0 {
		m["removeButton"] = resp.RemoveButton
	}
	if len(resp.ChangeButton) > 0 {
		m["changeButton"] = resp.ChangeButton
	}
	return m
}

// loadInputMethods 加载所有输入法
func loadInputMethods(server *Server) {
	// 获取当前目录
	exePath, err := os.Executable()
	if err != nil {
		log.Fatal("获取可执行文件路径失败:", err)
	}
	exeDir := filepath.Dir(exePath)

	// 扫描 input_methods 目录
	inputMethodsDir := filepath.Join(exeDir, "input_methods")
	entries, err := os.ReadDir(inputMethodsDir)
	if err != nil {
		log.Printf("读取 input_methods 目录失败: %v", err)
		return
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		// 读取 ime.json
		imePath := filepath.Join(inputMethodsDir, entry.Name(), "ime.json")
		data, err := os.ReadFile(imePath)
		if err != nil {
			log.Printf("读取 %s 失败: %v", imePath, err)
			continue
		}

		var imeConfig map[string]interface{}
		if err := json.Unmarshal(data, &imeConfig); err != nil {
			log.Printf("解析 %s 失败: %v", imePath, err)
			continue
		}

		guid, _ := imeConfig["guid"].(string)
		name, _ := imeConfig["name"].(string)
		guid = strings.ToLower(guid)
		if guid == "" {
			log.Printf("%s 缺少 guid", entry.Name())
			continue
		}

		log.Printf("加载输入法: %s (%s)", name, guid)

		// 根据输入法名称注册不同的服务实现
		switch entry.Name() {
		case "meow":
			// 喵喵输入法
			server.RegisterService(guid, func(client *pime.Client, g string) pime.TextService {
				return meow.New(client)
			})
		case "rime":
			// RIME 输入法
			server.RegisterService(guid, func(client *pime.Client, g string) pime.TextService {
				return rime.New(client)
			})
		case "simple_pinyin":
			// 拼音输入法
			server.RegisterService(guid, func(client *pime.Client, g string) pime.TextService {
				return simplepinyin.New(client)
			})
		case "fcitx5":
			// Fcitx5 输入法
			server.RegisterService(guid, func(client *pime.Client, g string) pime.TextService {
				return fcitx5.New(client)
			})
		default:
			// 默认使用拼音输入法
			server.RegisterService(guid, func(client *pime.Client, g string) pime.TextService {
				return simplepinyin.New(client)
			})
		}
	}
}

func openLogFile() (*os.File, error) {
	candidates := []string{}

	if localAppData := os.Getenv("LOCALAPPDATA"); localAppData != "" {
		candidates = append(candidates, filepath.Join(localAppData, "PIME", "Logs", "go_backend.log"))
	}
	if tempDir := os.TempDir(); tempDir != "" {
		candidates = append(candidates, filepath.Join(tempDir, "PIME", "go_backend.log"))
	}
	candidates = append(candidates, "go_backend.log")

	var lastErr error
	for _, logPath := range candidates {
		logDir := filepath.Dir(logPath)
		if logDir != "." && logDir != "" {
			if err := os.MkdirAll(logDir, 0755); err != nil {
				lastErr = err
				continue
			}
		}

		logFile, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
		if err == nil {
			return logFile, nil
		}
		lastErr = err
	}

	return nil, lastErr
}

func main() {
	// 日志优先写入用户可写目录，避免安装到 Program Files 后启动失败。
	logFile, err := openLogFile()
	if err != nil {
		log.SetOutput(os.Stderr)
		log.SetFlags(log.LstdFlags | log.Lshortfile)
		log.Printf("无法创建日志文件，改用标准错误输出: %v", err)
	} else {
		defer logFile.Close()
		log.SetOutput(logFile)
		log.SetFlags(log.LstdFlags | log.Lshortfile)
	}

	log.Println("=" + strings.Repeat("=", 50))
	log.Println("PIME Go 后端启动")
	log.Println("=" + strings.Repeat("=", 50))

	// 创建服务器
	server := NewServer()

	// 加载所有输入法
	loadInputMethods(server)

	// 运行服务器
	if err := server.Run(); err != nil {
		log.Fatal("服务器错误:", err)
	}
}
