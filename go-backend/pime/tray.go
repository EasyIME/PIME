package pime

import (
	"os"
	"path/filepath"
)

func sharedRimeIconPath(iconName string) string {
	exePath, err := os.Executable()
	if err != nil {
		return ""
	}
	iconPath := filepath.Join(filepath.Dir(exePath), "input_methods", "rime", "icons", iconName)
	if _, err := os.Stat(iconPath); err != nil {
		return ""
	}
	return iconPath
}

func modeIconName(asciiMode bool) string {
	if asciiMode {
		return "eng_half_capsoff.ico"
	}
	return "chi_half_capsoff.ico"
}

func langIconName(asciiMode bool) string {
	if asciiMode {
		return "eng.ico"
	}
	return "chi.ico"
}

func AddLangButtons(resp *Response, client *Client, asciiMode bool, modeCommandID int, langCommandID int) {
	if client != nil && client.IsWindows8Above {
		if iconPath := sharedRimeIconPath(modeIconName(asciiMode)); iconPath != "" {
			resp.AddButton = append(resp.AddButton, ButtonInfo{
				ID:        "windows-mode-icon",
				Icon:      iconPath,
				Tooltip:   "中西文切换",
				CommandID: modeCommandID,
			})
		}
	}
	if iconPath := sharedRimeIconPath(langIconName(asciiMode)); iconPath != "" {
		resp.AddButton = append(resp.AddButton, ButtonInfo{
			ID:        "switch-lang",
			Icon:      iconPath,
			Tooltip:   "中西文切换",
			CommandID: langCommandID,
		})
	}
}

func ChangeLangButtons(resp *Response, client *Client, asciiMode bool) {
	if client != nil && client.IsWindows8Above {
		if iconPath := sharedRimeIconPath(modeIconName(asciiMode)); iconPath != "" {
			resp.ChangeButton = append(resp.ChangeButton, ButtonInfo{
				ID:   "windows-mode-icon",
				Icon: iconPath,
			})
		}
	}
	if iconPath := sharedRimeIconPath(langIconName(asciiMode)); iconPath != "" {
		resp.ChangeButton = append(resp.ChangeButton, ButtonInfo{
			ID:   "switch-lang",
			Icon: iconPath,
		})
	}
}

func RemoveLangButtons(resp *Response, client *Client) {
	if client != nil && client.IsWindows8Above {
		resp.RemoveButton = append(resp.RemoveButton, "windows-mode-icon")
	}
	resp.RemoveButton = append(resp.RemoveButton, "switch-lang")
}
