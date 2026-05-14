# PIME Go 后端

使用 Go 语言实现的 PIME 输入法后端框架。

## 项目结构

```
go-backend/
├── pime/                 # PIME 核心库
│   ├── protocol.go     # 通信协议定义
│   ├── server.go       # 服务器实现
│   ├── service.go      # 文本服务接口
│   └── service_manager.go  # 服务管理器
├── input_methods/            # 示例实现
│   └── simple_ime/     # 简单输入法示例
│       ├── main.go     # 入口文件
│       └── ime.go      # 输入法实现
├── go.mod              # Go 模块定义
└── README.md           # 说明文档
```

## 快速开始

### 1. 编译

```bash
cd go-backend
build.bat
```

`build.bat` 会生成可直接安装的运行目录：

```text
build/
├── backends.go-backend.json
└── go-backend/
    ├── server.exe
    └── input_methods/
```

### 2. 配置 PIME

在 PIME 根目录的 `backends.json` 中添加 Go 后端配置。

注意：这个仓库里的 `backends.json` 顶层是数组，不是 `{ "backends": [...] }`。

```json
[
  {
    "name": "go-backend",
    "command": "go-backend\\server.exe",
    "workingDir": "go-backend",
    "params": ""
  }
]
```

### 3. 注册输入法

确保 `C:\Program Files (x86)\PIME\go-backend\input_methods\*\ime.json` 存在。比如：

```json
{
  "name": "GoSimpleIME",
  "icon": "icon.ico",
  "backend": "go-backend"
}
```

## 开发自定义输入法

### 1. 实现 TextService 接口

```go
type MyIME struct {
    *pime.TextServiceBase
    // 自定义字段
}

func NewMyIME(client *pime.Client) *MyIME {
    return &MyIME{
        TextServiceBase: pime.NewTextServiceBase(client),
    }
}

func (ime *MyIME) HandleRequest(req *pime.Request) *pime.Response {
    resp := pime.NewResponse(req.SeqNum, true)
    
    switch req.Method {
    case "filterKeyDown":
        // 处理按键
        return ime.handleKeyDown(req, resp)
    // ... 其他方法
    }
    
    return resp
}
```

### 2. 注册到服务管理器

```go
func main() {
    mgr := pime.NewServiceManager()
    
    // 注册输入法
    mgr.Register("my_ime", func(clientID string) pime.TextService {
        return NewMyIME(&pime.Client{ID: clientID})
    })
    
    // 运行服务
    if err := mgr.Run(); err != nil {
        log.Fatal(err)
    }
}
```

## 协议说明

### 通信方式

- 使用 stdin/stdout 进行通信
- 每行一条消息
- JSON 格式

### 请求格式

```
<client_id>|<JSON>
```

### 响应格式

```
PIME_MSG|<client_id>|<JSON>
```

### 消息类型

#### 初始化
```json
{
  "method": "init",
  "id": "client_guid",
  "isWindows8Above": true,
  "isMetroApp": false,
  "isUiLess": false,
  "isConsole": false
}
```

#### 按键处理
```json
{
  "method": "filterKeyDown",
  "keyCode": 65,
  "charCode": 97,
  "scanCode": 30
}
```

#### 响应
```json
{
  "success": true,
  "returnValue": 1,
  "compositionString": "a",
  "candidateList": ["啊", "阿", "吖"],
  "showCandidates": true
}
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

LGPL-2.1 License
