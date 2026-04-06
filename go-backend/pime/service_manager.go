// 服务管理器
package pime

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"sync"
)

// ServiceFactory 服务工厂函数类型
type ServiceFactory func(clientID string) TextService

// ServiceManager 服务管理器
type ServiceManager struct {
	mu        sync.RWMutex
	factories map[string]ServiceFactory
	services  map[string]TextService
	reader    *bufio.Reader
	running   bool
}

// NewServiceManager 创建服务管理器
func NewServiceManager() *ServiceManager {
	return &ServiceManager{
		factories: make(map[string]ServiceFactory),
		services:  make(map[string]TextService),
		reader:    bufio.NewReader(os.Stdin),
	}
}

// Register 注册服务工厂
func (m *ServiceManager) Register(name string, factory ServiceFactory) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.factories[name] = factory
}

// Run 运行服务管理器
func (m *ServiceManager) Run() error {
	m.running = true
	
	for m.running {
		line, err := m.reader.ReadString('\n')
		if err != nil {
			return err
		}
		
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		
		if err := m.handleMessage(line); err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		}
	}
	
	return nil
}

// handleMessage 处理消息
func (m *ServiceManager) handleMessage(line string) error {
	// 解析格式: "<client_id>|<JSON>"
	parts := strings.SplitN(line, "|", 2)
	if len(parts) != 2 {
		return fmt.Errorf("invalid message format")
	}
	
	clientID := parts[0]
	jsonStr := parts[1]
	
	// 解析 JSON
	var msg map[string]interface{}
	if err := json.Unmarshal([]byte(jsonStr), &msg); err != nil {
		return err
	}
	
	// 处理消息
	response := m.processMessage(clientID, msg)
	
	// 发送响应
	return m.sendResponse(clientID, response)
}

// processMessage 处理消息
func (m *ServiceManager) processMessage(clientID string, msg map[string]interface{}) map[string]interface{} {
	response := make(map[string]interface{})
	
	// 获取序列号
	if seqNum, ok := msg["seqNum"].(float64); ok {
		response["seqNum"] = int(seqNum)
	}
	
	// 获取方法
	method, _ := msg["method"].(string)
	
	switch method {
	case "init":
		// 初始化
		response["success"] = m.initClient(clientID, msg)
		
	case "close":
		// 关闭客户端
		m.closeClient(clientID)
		response["success"] = true
		
	default:
		// 其他方法，转发给服务处理
		if service := m.getService(clientID); service != nil {
			// 这里需要实现具体的请求处理
			response["success"] = true
		} else {
			response["success"] = false
		}
	}
	
	return response
}

// initClient 初始化客户端
func (m *ServiceManager) initClient(clientID string, msg map[string]interface{}) bool {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	// 创建默认服务（使用第一个注册的工厂）
	for _, factory := range m.factories {
		service := factory(clientID)
		m.services[clientID] = service
		return true
	}
	
	return false
}

// closeClient 关闭客户端
func (m *ServiceManager) closeClient(clientID string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	
	if service, ok := m.services[clientID]; ok {
		service.Close()
		delete(m.services, clientID)
	}
}

// getService 获取服务
func (m *ServiceManager) getService(clientID string) TextService {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.services[clientID]
}

// sendResponse 发送响应
func (m *ServiceManager) sendResponse(clientID string, response map[string]interface{}) error {
	data, err := json.Marshal(response)
	if err != nil {
		return err
	}
	
	line := fmt.Sprintf("PIME_MSG|%s|%s\n", clientID, string(data))
	_, err = os.Stdout.WriteString(line)
	return err
}
