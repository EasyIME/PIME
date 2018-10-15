import time
from contextlib import contextmanager

from ctypes import *
from ctypes.wintypes import *

LRESULT = LPARAM
WNDPROC = WINFUNCTYPE(LRESULT, HWND, c_uint, WPARAM, LPARAM)

WM_QUIT = 0
WM_CREATE = 0x0001
WM_CLIPBOARDUPDATE = 0x031D

WS_OVERLAPPEDWINDOW = 0xcf0000

GHND = 0x0042


# https://gist.github.com/mouseroot/6128651
class WNDCLASSEX(Structure):
    _fields_ = [
        ("cbSize", c_uint),
        ("style", c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", c_int),
        ("cbWndExtra", c_int),
        ("hInstance", HANDLE),
        ("hIcon", HANDLE),
        ("hCursor", HANDLE),
        ("hBrush", HANDLE),
        ("lpszMenuName", LPCWSTR),
        ("lpszClassName", LPCWSTR),
        ("hIconSm", HANDLE)
    ]


def register_window_class(class_name, wnd_proc_ptr):
    hinst = windll.kernel32.GetModuleHandleW(0)

    # register
    wndClass = WNDCLASSEX()
    wndClass.cbSize = sizeof(WNDCLASSEX)
    wndClass.style = 0
    wndClass.lpfnWndProc = wnd_proc_ptr
    wndClass.cbClsExtra = 0
    wndClass.cbWndExtra = 0
    wndClass.hInstance = hinst
    wndClass.hIcon = 0
    wndClass.hCursor = 0
    wndClass.hBrush = 0
    wndClass.lpszMenuName = 0
    wndClass.lpszClassName = class_name
    wndClass.hIconSm = 0

    reg = windll.user32.RegisterClassExW(byref(wndClass))
    return reg


def create_window(class_name, text='', style=WS_OVERLAPPEDWINDOW):
    hinst = windll.kernel32.GetModuleHandleW(0)
    hwnd = windll.user32.CreateWindowExW(0, class_name, text,
                                         style, 0, 0, 0, 0,
                                         0, 0, hinst, 0)
    return hwnd


def run_windows_message_loop():
    msg = MSG()
    pmsg = byref(msg)
    while windll.user32.GetMessageW(pmsg, 0, 0, 0) > 0:
        windll.user32.TranslateMessage(pmsg)
        windll.user32.DispatchMessageW(pmsg)


@contextmanager
def open_clipboard(hwnd, retry=True, timeout=1.0):
    opened = False
    start_time = time.time()
    # lock the clipboard
    while True:
        # keep trying until we succeed or timeout
        opened = windll.user32.OpenClipboard(hwnd)
        if opened or not retry or (time.time() - start_time) >= timeout:
            break
    try:
        yield opened
    finally:
        if opened:
            windll.user32.CloseClipboard()


def get_clipboard_data(data_format):
    hmem = windll.user32.GetClipboardData(data_format)
    if hmem:
        # lock memory address of the clipboard data
        ptr = windll.kernel32.GlobalLock(hmem)
        size = windll.kernel32.GlobalSize(hmem)
        # copy the data to our own buffer
        buffer = create_string_buffer(size)
        memmove(buffer, ptr, size)
        windll.kernel32.GlobalUnlock(hmem)
        # return the data as bytes
        return buffer.raw
    return None


def set_clipboard_data(data_format, data):
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError('data needs to be byte-like objects')
    size = len(data)
    hmem = windll.kernel32.GlobalAlloc(GHND, size)
    ptr = windll.kernel32.GlobalLock(hmem)
    buf = c_char_p(data)
    memmove(ptr, buf, size)
    windll.kernel32.GlobalUnlock(hmem)
    ret = windll.user32.SetClipboardData(data_format, hmem)
    return ret
