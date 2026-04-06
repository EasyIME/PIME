// PIME 服务器实现
package pime

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"sync"
)

// Handler 请求处理函数类型
type Handler func(clientID string, req *Request) *Response

// Server PIME 服务器
type Server struct {
	mu       sync.RWMutex
	handlers map[string]Handler
	clients  map[string]*Client
	reader   *bufio.Reader
	writer   io.Writer
	running  bool
}

// Client 客户端连接
type Client struct {
	ID              string
	GUID            string
	IsWindows8Above bool
	IsMetroApp      bool
	IsUiLess        bool
	IsConsole       bool
	Service         TextService
}

// TextService 文本服务接口
type TextService interface {
	Init(req *Request) bool
	HandleRequest(req *Request) *Response
	Close()
}

// NewServer 创建新服务器
func NewServer() *Server {
	return &Server{
		handlers: make(map[string]Handler),
		clients:  make(map[string]*Client),
		reader:   bufio.NewReader(os.Stdin),
		writer:   os.Stdout,
	}
}

// SetIO 设置自定义输入输出（用于测试）
func (s *Server) SetIO(reader io.Reader, writer io.Writer) {
	s.reader = bufio.NewReader(reader)
	s.writer = writer
}

// RegisterHandler 注册方法处理器
func (s *Server) RegisterHandler(method string, handler Handler) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.handlers[method] = handler
}

// Run 运行服务器
func (s *Server) Run() error {
	s.running = true
	
	for s.running {
		line, err := s.reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				return nil
			}
			return fmt.Errorf("read error: %w", err)
		}
		
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		
		if err := s.handleMessage(line); err != nil {
			fmt.Fprintf(os.Stderr, "handle message error: %v\n", err)
		}
	}
	
	return nil
}

// Stop 停止服务器
func (s *Server) Stop() {
	s.running = false
}

// handleMessage 处理消息
func (s *Server) handleMessage(line string) error {
	// 解析消息格式: "<client_id>|<JSON>"
	parts := strings.SplitN(line, "|", 2)
	if len(parts) != 2 {
		return fmt.Errorf("invalid message format")
	}
	
	clientID := parts[0]
	jsonData := parts[1]
	
	// 解析 JSON 请求
	var req Request
	if err := json.Unmarshal([]byte(jsonData), &req); err != nil {
		return fmt.Errorf("unmarshal request failed: %w", err)
	}
	
	// 处理请求
	var resp *Response
	
	// 特殊处理 init 方法
	if req.Method == "" && req.ID.StringValue() != "" {
		// 初始化请求
		resp = s.handleInit(clientID, &req)
	} else if handler, ok := s.handlers[req.Method]; ok {
		resp = handler(clientID, &req)
	} else {
		// 默认处理
		resp = NewResponse(req.SeqNum, true)
	}
	
	// 发送响应
	return s.sendResponse(clientID, resp)
}

// handleInit 处理初始化
func (s *Server) handleInit(clientID string, req *Request) *Response {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	// 创建客户端
	client := &Client{
		ID:              clientID,
		IsWindows8Above: req.IsWindows8Above,
		IsMetroApp:      req.IsMetroApp,
		IsUiLess:        req.IsUiLess,
		IsConsole:       req.IsConsole,
	}
	s.clients[clientID] = client
	
	resp := NewResponse(req.SeqNum, true)
	return resp
}

// sendResponse 发送响应
func (s *Server) sendResponse(clientID string, resp *Response) error {
	// 格式: "PIME_MSG|<client_id>|<JSON>"
	jsonData, err := resp.ToJSON()
	if err != nil {
		return err
	}
	
	line := fmt.Sprintf("PIME_MSG|%s|%s\n", clientID, string(jsonData))
	_, err = s.writer.Write([]byte(line))
	return err
}

// GetClient 获取客户端
func (s *Server) GetClient(clientID string) *Client {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.clients[clientID]
}

// RemoveClient 移除客户端
func (s *Server) RemoveClient(clientID string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if client, ok := s.clients[clientID]; ok {
		if client.Service != nil {
			client.Service.Close()
		}
		delete(s.clients, clientID)
	}
}
