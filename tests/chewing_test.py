# python3
# coding=utf8
from ctypes import *
import random
import os
import time


VK_CONTROL = 0x11
VK_MENU = 0x12
VK_TAB = 0x09
VK_RETURN = 0x13
VK_ESCAPE = 0X1b
VK_SHIFT = 0x10

VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28

KEYEVENTF_KEYUP = 0x0002

keybd_event = windll.user32.keybd_event
VkKeyScan = windll.user32.VkKeyScanA
GetTopWindow = windll.user32.GetTopWindow
GetWindow = windll.user32.GetWindow
GetWindowText = windll.user32.GetWindowTextW
IsWindowVisible = windll.user32.IsWindowVisible
SetForegroundWindow = windll.user32.SetForegroundWindow
GetForegroundWindow = windll.user32.GetForegroundWindow
SwitchToThisWindow = windll.user32.SwitchToThisWindow
ShowWindow = windll.user32.ShowWindow
GetWindowThreadProcessId = windll.user32.GetWindowThreadProcessId
AttachThreadInput = windll.user32.AttachThreadInput
GetCurrentThreadId = windll.kernel32.GetCurrentThreadId
BringWindowToTop = windll.user32.BringWindowToTop
SetFocus = windll.user32.SetFocus


bopomofo_to_key = {}
phrases = []
target_windows = []


def press_key(key, delay=0.05, hold=0.02):
    if isinstance(key, str):  # ASCII 轉成 Windows virtual key code
        vk = VkKeyScan(ord(key)) & 0xff
    else:
        vk = key
    keybd_event(vk, 0, 0, 0)
    time.sleep(hold)
    keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(delay)


def activate_window(hwnd):
    fid = GetWindowThreadProcessId(GetForegroundWindow(), None)
    tid = GetWindowThreadProcessId(hwnd, None)
    AttachThreadInput(tid, fid, True)
    # BringWindowToTop(hwnd)
    # ShowWindow(hwnd, 2)
    SwitchToThisWindow(hwnd, True)
    SetFocus(hwnd)
    time.sleep(2)
    AttachThreadInput(tid, fid, False)


# 載入辭庫 注音 & 按鍵
def load_phrases():
    # 注音符號 => 鍵盤按鍵
    global bopomofo_to_key
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "phone.cin.txt"), "r", encoding="utf-8") as f:
        in_key = False
        for line in f:
            if not in_key:
                if line.startswith("%keyname  begin"):
                    in_key = True
            else:
                if line.startswith("%keyname  end"):
                    in_key = False
                else:
                    # 格式: <鍵盤按鍵> <注音符號>
                    parts = line.strip().split()
                    key = parts[0]
                    bopomofo = parts[1]
                    bopomofo_to_key[bopomofo] = key

    # 載入辭庫
    global phrases
    with open(os.path.join(dirname, "tsi.src.txt"), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 檔案格式: <詞彙> <頻率> <注音符號>
            parts = line.split('#')  # strip comments
            line = parts[0]
            parts = line.split(maxsplit=2)
            phrase = parts[0]
            bopomofo_sequence = parts[2]
            keys = []
            for p in bopomofo_sequence:
                if p == ' ':
                    # 如果注音符號結尾不是二三四聲或輕聲符號，補上空白(一聲)
                    if keys[-1] not in ('3', '4', '6', '7'):
                        keys.append(' ')
                    continue
                key = bopomofo_to_key[p]  # 注音符號轉成鍵盤按鍵
                keys.append(key)
            # 如果注音符號結尾不是二三四聲或輕聲符號，補上空白(一聲)
            if keys[-1] not in ('3', '4', '6', '7'):
                keys.append(' ')

            if len(phrase) >= 2:  # 只保留兩字以上的詞彙
                phrases.append((phrase, keys))


def prepare_test():
    visible_windows = []
    i = 1
    hwnd = GetTopWindow(None)
    text = create_unicode_buffer(256)
    while hwnd:
        text_len = GetWindowText(hwnd, text, 256)
        if IsWindowVisible(hwnd) and text.value and text_len > 0:
            try:
                print(i, text.value)
                visible_windows.append(hwnd)
                i += 1
            except UnicodeEncodeError:
                pass
        hwnd = GetWindow(hwnd, 2)  # GW_HWNDNEXT = 2

    print("-" * 80)
    print("目標視窗內必須先啟用新酷音輸入法...")

    global target_windows
    for i in input("輸入要測試的目標視窗代號 (以空白分隔):").strip().split():
        i = int(i) - 1
        hwnd = visible_windows[i]
        ShowWindow(hwnd, 9)  # SW_RESTORE = 9
        target_windows.append(hwnd)


def run_test():
    if not phrases or not target_windows:
        return

    try:
        n = int(input("請輸入測試次數 (預設 1000):"))
    except ValueError:
        n = 1000

    time.sleep(6)
    activate_window(random.choice(target_windows))
    time.sleep(1)

    for i in range(n):
        phrase, keys = random.choice(phrases)
        try:
            print(i, phrase, keys)
        except UnicodeEncodeError:
            pass

        for key in keys:
            press_key(key)

        # 按下 Enter (25% 機率發生)
        if random.random() < 0.25:
            press_key('\r')
            press_key('\r')

        # 按下 Ctrl + space (30% 機率發生)
        if random.random() < 0.3:
            time.sleep(0.5)
            keybd_event(VK_CONTROL, 0, 0, 0)
            press_key(' ')
            keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.5)

        # 按下 shift  0.3 秒後後放開 (30% 機率發生)
        if random.random() < 0.3:
            press_key(VK_SHIFT, hold=0.3)

        # 按下[下方向鍵] 開啟選字 (20% 機率發生)
        # 中文模式下則會開啟選字，若目前在英文模式下，會造成移動游標，而不會有其他作用。
        if random.random() < 0.2:
            press_key(VK_DOWN)
            time.sleep(1.5)
            if random.random() < 0.2:  # (20% 發生機率)
                press_key('1')  # 若選字清單已開，選擇第一個字。(若在英文模式下，會輸出數字 1)
            else:
                press_key(VK_ESCAPE)  # 按下 ESC 關閉選字清單

        # 切換視窗 (20% 發生率)
        if len(target_windows) > 1 and random.random() < 0.2:
            """
            # Alt + Tab
            time.sleep(0.5)
            keybd_event(VK_MENU, 0, 0, 0)
            press_key(VK_TAB)
            keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.5)
            """
            time.sleep(0.5)
            activate_window(random.choice(target_windows))
            time.sleep(0.5)



if __name__ == "__main__":
    random.seed()
    load_phrases()
    prepare_test()
    run_test()
