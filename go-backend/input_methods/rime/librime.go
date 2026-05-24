//go:build windows

// RIME Windows DLL 动态加载封装
// 参考 python/librime.py
package rime

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"syscall"
	"unsafe"
)

const (
	RIME_MAX_NUM_CANDIDATES = 10
)

type RimeSessionId uintptr

type RimeTraits struct {
	SharedDataDir        string
	UserDataDir          string
	DistributionName     string
	DistributionCodeName string
	DistributionVersion  string
	AppName              string
	Modules              []string
}

type RimeComposition struct {
	Length    int
	CursorPos int
	SelStart  int
	SelEnd    int
	Preedit   string
}

type RimeCandidate struct {
	Text    string
	Comment string
}

type RimeMenu struct {
	PageSize                  int
	PageNo                    int
	IsLastPage                bool
	HighlightedCandidateIndex int
	NumCandidates             int
	Candidates                []RimeCandidate
	SelectKeys                string
}

type RimeCommit struct {
	Text string
}

type NotificationHandler func(session RimeSessionId, messageType, messageValue string)

type rimeTraitsC struct {
	DataSize             int32
	SharedDataDir        *byte
	UserDataDir          *byte
	DistributionName     *byte
	DistributionCodeName *byte
	DistributionVersion  *byte
	AppName              *byte
	Modules              **byte
}

type rimeCompositionC struct {
	Length    int32
	CursorPos int32
	SelStart  int32
	SelEnd    int32
	Preedit   *byte
}

type rimeCandidateC struct {
	Text     *byte
	Comment  *byte
	Reserved uintptr
}

type rimeMenuC struct {
	PageSize                  int32
	PageNo                    int32
	IsLastPage                int32
	HighlightedCandidateIndex int32
	NumCandidates             int32
	Candidates                *rimeCandidateC
	SelectKeys                *byte
}

type rimeCommitC struct {
	DataSize int32
	Text     *byte
}

type rimeContextC struct {
	DataSize          int32
	Composition       rimeCompositionC
	Menu              rimeMenuC
	CommitTextPreview *byte
	SelectLabels      **byte
}

var (
	rimeDLLMu sync.Mutex
	rimeDLL   *syscall.LazyDLL
	rimeProcs struct {
		setup                 *syscall.LazyProc
		initialize            *syscall.LazyProc
		finalize              *syscall.LazyProc
		startMaintenance      *syscall.LazyProc
		joinMaintenanceThread *syscall.LazyProc
		deployConfigFile      *syscall.LazyProc
		createSession         *syscall.LazyProc
		findSession           *syscall.LazyProc
		destroySession        *syscall.LazyProc
		processKey            *syscall.LazyProc
		clearComposition      *syscall.LazyProc
		getCommit             *syscall.LazyProc
		freeCommit            *syscall.LazyProc
		getContext            *syscall.LazyProc
		freeContext           *syscall.LazyProc
		setOption             *syscall.LazyProc
		getOption             *syscall.LazyProc
		getVersion            *syscall.LazyProc
	}
)

func loadRimeDLL(dllPath string) error {
	rimeDLLMu.Lock()
	defer rimeDLLMu.Unlock()

	if rimeDLL != nil {
		return nil
	}

	if dllPath == "" {
		dllPath = "rime.dll"
	}
	dll := syscall.NewLazyDLL(dllPath)
	procs := struct {
		setup                 *syscall.LazyProc
		initialize            *syscall.LazyProc
		finalize              *syscall.LazyProc
		startMaintenance      *syscall.LazyProc
		joinMaintenanceThread *syscall.LazyProc
		deployConfigFile      *syscall.LazyProc
		createSession         *syscall.LazyProc
		findSession           *syscall.LazyProc
		destroySession        *syscall.LazyProc
		processKey            *syscall.LazyProc
		clearComposition      *syscall.LazyProc
		getCommit             *syscall.LazyProc
		freeCommit            *syscall.LazyProc
		getContext            *syscall.LazyProc
		freeContext           *syscall.LazyProc
		setOption             *syscall.LazyProc
		getOption             *syscall.LazyProc
		getVersion            *syscall.LazyProc
	}{
		setup:                 dll.NewProc("RimeSetup"),
		initialize:            dll.NewProc("RimeInitialize"),
		finalize:              dll.NewProc("RimeFinalize"),
		startMaintenance:      dll.NewProc("RimeStartMaintenance"),
		joinMaintenanceThread: dll.NewProc("RimeJoinMaintenanceThread"),
		deployConfigFile:      dll.NewProc("RimeDeployConfigFile"),
		createSession:         dll.NewProc("RimeCreateSession"),
		findSession:           dll.NewProc("RimeFindSession"),
		destroySession:        dll.NewProc("RimeDestroySession"),
		processKey:            dll.NewProc("RimeProcessKey"),
		clearComposition:      dll.NewProc("RimeClearComposition"),
		getCommit:             dll.NewProc("RimeGetCommit"),
		freeCommit:            dll.NewProc("RimeFreeCommit"),
		getContext:            dll.NewProc("RimeGetContext"),
		freeContext:           dll.NewProc("RimeFreeContext"),
		setOption:             dll.NewProc("RimeSetOption"),
		getOption:             dll.NewProc("RimeGetOption"),
		getVersion:            dll.NewProc("RimeGetVersion"),
	}

	for _, proc := range []*syscall.LazyProc{
		procs.setup, procs.initialize, procs.finalize, procs.startMaintenance, procs.joinMaintenanceThread,
		procs.deployConfigFile, procs.createSession, procs.findSession, procs.destroySession, procs.processKey,
		procs.clearComposition, procs.getCommit, procs.freeCommit, procs.getContext, procs.freeContext,
		procs.setOption, procs.getOption,
	} {
		if err := proc.Find(); err != nil {
			return err
		}
	}

	rimeDLL = dll
	rimeProcs = procs
	return nil
}

func utf8Ptr(s string) *byte {
	if s == "" {
		return nil
	}
	ptr, _ := syscall.BytePtrFromString(s)
	return ptr
}

func cString(ptr *byte) string {
	if ptr == nil {
		return ""
	}
	bytes := make([]byte, 0, 32)
	for p := uintptr(unsafe.Pointer(ptr)); ; p++ {
		b := *(*byte)(unsafe.Pointer(p))
		if b == 0 {
			break
		}
		bytes = append(bytes, b)
	}
	return string(bytes)
}

func boolResult(r1 uintptr) bool {
	return r1 != 0
}

func Init(traits RimeTraits) bool {
	cTraits := rimeTraitsC{
		DataSize:             int32(unsafe.Sizeof(rimeTraitsC{})) - 4,
		SharedDataDir:        utf8Ptr(traits.SharedDataDir),
		UserDataDir:          utf8Ptr(traits.UserDataDir),
		DistributionName:     utf8Ptr(traits.DistributionName),
		DistributionCodeName: utf8Ptr(traits.DistributionCodeName),
		DistributionVersion:  utf8Ptr(traits.DistributionVersion),
		AppName:              utf8Ptr(traits.AppName),
	}

	r1, _, _ := rimeProcs.setup.Call(uintptr(unsafe.Pointer(&cTraits)))
	runtime.KeepAlive(cTraits)
	return boolResult(r1) || true
}

func Finalize() {
	rimeProcs.finalize.Call()
}

func StartSession() (RimeSessionId, bool) {
	r1, _, _ := rimeProcs.createSession.Call()
	return RimeSessionId(r1), r1 != 0
}

func FindSession(sessionId RimeSessionId) bool {
	if sessionId == 0 {
		return false
	}
	r1, _, _ := rimeProcs.findSession.Call(uintptr(sessionId))
	return boolResult(r1)
}

func EndSession(sessionId RimeSessionId) {
	if sessionId != 0 {
		rimeProcs.destroySession.Call(uintptr(sessionId))
	}
}

func ProcessKey(sessionId RimeSessionId, keyCode, modifiers int) bool {
	r1, _, _ := rimeProcs.processKey.Call(uintptr(sessionId), uintptr(keyCode), uintptr(modifiers))
	return boolResult(r1)
}

func ClearComposition(sessionId RimeSessionId) {
	rimeProcs.clearComposition.Call(uintptr(sessionId))
}

func GetComposition(sessionId RimeSessionId) (RimeComposition, bool) {
	context, ok := getContext(sessionId)
	if !ok {
		return RimeComposition{}, false
	}
	defer freeContext(&context)

	return RimeComposition{
		Length:    int(context.Composition.Length),
		CursorPos: int(context.Composition.CursorPos),
		SelStart:  int(context.Composition.SelStart),
		SelEnd:    int(context.Composition.SelEnd),
		Preedit:   cString(context.Composition.Preedit),
	}, true
}

func GetMenu(sessionId RimeSessionId) (RimeMenu, bool) {
	context, ok := getContext(sessionId)
	if !ok {
		return RimeMenu{}, false
	}
	defer freeContext(&context)

	menu := RimeMenu{
		PageSize:                  int(context.Menu.PageSize),
		PageNo:                    int(context.Menu.PageNo),
		IsLastPage:                context.Menu.IsLastPage != 0,
		HighlightedCandidateIndex: int(context.Menu.HighlightedCandidateIndex),
		NumCandidates:             int(context.Menu.NumCandidates),
		SelectKeys:                cString(context.Menu.SelectKeys),
	}

	if context.Menu.NumCandidates > 0 && context.Menu.Candidates != nil {
		candidates := unsafe.Slice(context.Menu.Candidates, int(context.Menu.NumCandidates))
		menu.Candidates = make([]RimeCandidate, 0, len(candidates))
		for _, candidate := range candidates {
			menu.Candidates = append(menu.Candidates, RimeCandidate{
				Text:    cString(candidate.Text),
				Comment: cString(candidate.Comment),
			})
		}
	}
	return menu, true
}

func GetCommit(sessionId RimeSessionId) (RimeCommit, bool) {
	commit := rimeCommitC{DataSize: int32(unsafe.Sizeof(rimeCommitC{})) - 4}
	r1, _, _ := rimeProcs.getCommit.Call(uintptr(sessionId), uintptr(unsafe.Pointer(&commit)))
	if !boolResult(r1) {
		return RimeCommit{}, false
	}
	defer rimeProcs.freeCommit.Call(uintptr(unsafe.Pointer(&commit)))
	return RimeCommit{Text: cString(commit.Text)}, true
}

func SetOption(sessionId RimeSessionId, option string, value bool) {
	name := utf8Ptr(option)
	var v uintptr
	if value {
		v = 1
	}
	rimeProcs.setOption.Call(uintptr(sessionId), uintptr(unsafe.Pointer(name)), v)
	runtime.KeepAlive(name)
}

func GetOption(sessionId RimeSessionId, option string) bool {
	name := utf8Ptr(option)
	r1, _, _ := rimeProcs.getOption.Call(uintptr(sessionId), uintptr(unsafe.Pointer(name)))
	runtime.KeepAlive(name)
	return boolResult(r1)
}

func SelectCandidate(sessionId RimeSessionId, index int) {
	_ = sessionId
	_ = index
}

func SelectPage(sessionId RimeSessionId, pageNo int) {
	_ = sessionId
	_ = pageNo
}

func DeployConfigFile(filePath, key string) bool {
	cFile := utf8Ptr(filePath)
	cKey := utf8Ptr(key)
	r1, _, _ := rimeProcs.deployConfigFile.Call(uintptr(unsafe.Pointer(cFile)), uintptr(unsafe.Pointer(cKey)))
	runtime.KeepAlive(cFile)
	runtime.KeepAlive(cKey)
	return boolResult(r1)
}

func SetNotificationHandler(handler NotificationHandler) {
	_ = handler
}

func APIVersion() string {
	return ""
}

func GetName() string {
	return ""
}

func GetVersion() string {
	if rimeProcs.getVersion == nil {
		return ""
	}
	if err := rimeProcs.getVersion.Find(); err != nil {
		return ""
	}
	r1, _, _ := rimeProcs.getVersion.Call()
	return cString((*byte)(unsafe.Pointer(r1)))
}

func RimeInit(datadir, userdir, appname, appver string, fullcheck bool) bool {
	if err := os.MkdirAll(userdir, 0700); err != nil {
		log.Printf("创建用户目录失败: %v", err)
		return false
	}

	dllPath := filepath.Join(filepath.Dir(datadir), "rime.dll")
	if _, err := os.Stat(dllPath); err != nil {
		dllPath = "rime.dll"
	}
	if err := loadRimeDLL(dllPath); err != nil {
		log.Printf("加载 RIME DLL 失败: %v", err)
		return false
	}

	traits := RimeTraits{
		SharedDataDir:        datadir,
		UserDataDir:          userdir,
		DistributionName:     "Rime",
		DistributionCodeName: appname,
		DistributionVersion:  appver,
		AppName:              fmt.Sprintf("Rime.%s", appname),
	}
	if !Init(traits) {
		log.Println("RIME setup 失败")
		return false
	}

	rimeProcs.initialize.Call(0)
	var fullcheckArg uintptr
	if fullcheck {
		fullcheckArg = 1
	}
	r1, _, _ := rimeProcs.startMaintenance.Call(fullcheckArg)
	if boolResult(r1) {
		rimeProcs.joinMaintenanceThread.Call()
	}

	configFiles := []string{
		filepath.Join(datadir, appname+".yaml"),
		filepath.Join(userdir, appname+".yaml"),
		filepath.Join(userdir, "default.custom.yaml"),
	}
	for _, configFile := range configFiles {
		if _, err := os.Stat(configFile); err != nil {
			continue
		}
		if !DeployConfigFile(configFile, "config_version") {
			log.Printf("部署配置文件失败: %s", configFile)
			return false
		}
	}
	return true
}

func getContext(sessionId RimeSessionId) (rimeContextC, bool) {
	context := rimeContextC{DataSize: int32(unsafe.Sizeof(rimeContextC{})) - 4}
	r1, _, _ := rimeProcs.getContext.Call(uintptr(sessionId), uintptr(unsafe.Pointer(&context)))
	if !boolResult(r1) {
		return rimeContextC{}, false
	}
	return context, true
}

func freeContext(context *rimeContextC) {
	rimeProcs.freeContext.Call(uintptr(unsafe.Pointer(context)))
}
