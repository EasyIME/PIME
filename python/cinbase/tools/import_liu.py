"""
Standalone Liu (Boshiamy) Table Importer Tool for PIME.
Allows the user to select their legally owned liu-uni.tab file,
converts it to liu.cin and then compiles it into JSON for PIME cinbase.
"""

import os
import sys
import subprocess
import ctypes
from ctypes import wintypes


class OPENFILENAMEW(ctypes.Structure):
    _fields_ = [
        ("lStructSize", wintypes.DWORD),
        ("hwndOwner", wintypes.HWND),
        ("hInstance", wintypes.HINSTANCE),
        ("lpstrFilter", wintypes.LPCWSTR),
        ("lpstrCustomFilter", wintypes.LPWSTR),
        ("nMaxCustFilter", wintypes.DWORD),
        ("nFilterIndex", wintypes.DWORD),
        ("lpstrFile", wintypes.LPWSTR),
        ("nMaxFile", wintypes.DWORD),
        ("lpstrFileTitle", wintypes.LPWSTR),
        ("nMaxFileTitle", wintypes.DWORD),
        ("lpstrInitialDir", wintypes.LPCWSTR),
        ("lpstrTitle", wintypes.LPCWSTR),
        ("Flags", wintypes.DWORD),
        ("nFileOffset", wintypes.WORD),
        ("nFileExtension", wintypes.WORD),
        ("lpstrDefExt", wintypes.LPCWSTR),
        ("lCustData", wintypes.LPARAM),
        ("lpfnHook", wintypes.LPVOID),
        ("lpTemplateName", wintypes.LPCWSTR),
        ("pvReserved", wintypes.LPVOID),
        ("dwReserved", wintypes.DWORD),
        ("FlagsEx", wintypes.DWORD),
    ]


def browse_for_file():
    OFN_FILEMUSTEXIST = 0x00001000
    OFN_PATHMUSTEXIST = 0x00000800

    buf = ctypes.create_unicode_buffer(1024)
    filter_str = "liu-uni.tab (*.tab)\0*.tab\0All Files (*.*)\0*.*\0\0"

    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.lpstrFilter = filter_str
    ofn.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR)
    ofn.nMaxFile = 1024
    ofn.lpstrTitle = "Select Boshiamy (liu-uni.tab) Table File / 選取嘸蝦米碼表檔案"
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST

    if ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
        return buf.value
    return None


def main():
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    cinbase_dir = os.path.dirname(tools_dir)
    pime_python_dir = os.path.dirname(cinbase_dir)

    python_exe = os.path.join(pime_python_dir, "python3", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    tab_file = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        tab_file = sys.argv[1]
    else:
        # Prompt user to browse
        MB_OKCANCEL = 0x1
        MB_ICONQUESTION = 0x20
        IDOK = 1
        ret = ctypes.windll.user32.MessageBoxW(
            0,
            "嘸蝦米輸入法需要您合法擁有的 liu-uni.tab 碼表檔案。\n現在是否要選取該檔案？\n\n"
            "Shiamy (Liu) input method requires your licensed liu-uni.tab table file.\n"
            "Would you like to locate it now?",
            "PIME - Shiamy Setup / 嘸蝦米設定",
            MB_OKCANCEL | MB_ICONQUESTION
        )
        if ret == IDOK:
            tab_file = browse_for_file()

    if not tab_file or not os.path.exists(tab_file):
        print("No liu-uni.tab file selected. Skipping Shiamy setup.")
        return

    user_data_dir = os.path.join(os.environ.get("APPDATA", ""), "PIME", "cheliu")
    os.makedirs(user_data_dir, exist_ok=True)
    out_cin = os.path.join(user_data_dir, "liu.cin")
    out_json = os.path.join(user_data_dir, "liu.json")

    # Clean up stale outputs before conversion so old files don't mask failures
    for path in (out_cin, out_json):
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    unitab2cin = os.path.join(tools_dir, "liu_unitab2cin.py")
    cintojson = os.path.join(tools_dir, "cintojson.py")

    create_no_window = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

    print(f"Converting {tab_file} to {out_cin}...")
    ret1 = subprocess.call(
        [python_exe, unitab2cin, tab_file, out_cin],
        creationflags=create_no_window
    )

    if ret1 == 0 and os.path.exists(out_cin):
        print("Converting liu.cin to JSON...")
        ret2 = subprocess.call(
            [python_exe, cintojson, out_cin, "nosort", user_data_dir],
            cwd=tools_dir,
            creationflags=create_no_window
        )
        if ret2 == 0 and os.path.exists(out_json):
            ctypes.windll.user32.MessageBoxW(
                0,
                "嘸蝦米碼表已成功匯入！\n若輸入法正在使用中，請重新啟動應用程式以載入新碼表。\n\n"
                "Shiamy (Liu) table imported successfully!\n"
                "If the input method is currently active, please restart applications to load the new table.",
                "PIME - Shiamy Setup / 嘸蝦米設定",
                0x40  # MB_ICONINFORMATION
            )
            return

    ctypes.windll.user32.MessageBoxW(
        0,
        "轉換 liu-uni.tab 碼表失敗。\n\nFailed to convert liu-uni.tab file.",
        "PIME - Shiamy Setup / 嘸蝦米設定",
        0x10  # MB_ICONSTOP
    )


if __name__ == '__main__':
    main()
