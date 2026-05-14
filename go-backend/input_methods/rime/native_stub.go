//go:build !windows

package rime

func newNativeBackend() rimeBackend {
	return nil
}
