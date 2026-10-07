"""
Standalone Liu (Boshiamy) Table Importer Tool for PIME.
Allows the user to select their legally owned liu-uni.tab file,
converts it to liu.cin and then compiles it into JSON for PIME cinbase.
"""

import os
import sys
import subprocess
import ctypes

import ctypes.wintypes

def browse_for_file():
    class OPENFILENAMEW(ctypes.Structure):
        _fields_ = [
            ("lStructSize", ctypes.wintypes.DWORD),
            ("hwndOwner", ctypes.wintypes.HWND),
            ("hInstance", ctypes.wintypes.HINSTANCE),
            ("lpstrFilter", ctypes.c_wchar_p),
            ("lpstrCustomFilter", ctypes.c_wchar_p),
            ("nMaxCustFilter", ctypes.wintypes.DWORD),
            ("nFilterIndex", ctypes.wintypes.DWORD),
            ("lpstrFile", ctypes.c_wchar_p),
            ("nMaxFile", ctypes.wintypes.DWORD),
            ("lpstrFileTitle", ctypes.c_wchar_p),
            ("nMaxFileTitle", ctypes.wintypes.DWORD),
            ("lpstrInitialDir", ctypes.c_wchar_p),
            ("lpstrTitle", ctypes.c_wchar_p),
            ("Flags", ctypes.wintypes.DWORD),
            ("nFileOffset", ctypes.wintypes.WORD),
            ("nFileExtension", ctypes.wintypes.WORD),
            ("lpstrDefExt", ctypes.c_wchar_p),
            ("lCustData", ctypes.wintypes.LPARAM),
            ("lpfnHook", ctypes.c_void_p),
            ("lpTemplateName", ctypes.c_wchar_p),
            ("pvReserved", ctypes.c_void_p),
            ("dwReserved", ctypes.wintypes.DWORD),
            ("FlagsEx", ctypes.wintypes.DWORD)
        ]

    MAX_PATH = 260
    OFN_FILEMUSTEXIST = 0x00001000
    OFN_PATHMUSTEXIST = 0x00000800

    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.hwndOwner = 0
    
    filter_str = "liu-uni.tab (*.tab)\0*.tab\0All Files (*.*)\0*.*\0\0"
    ofn.lpstrFilter = filter_str
    
    file_buffer = ctypes.create_unicode_buffer(MAX_PATH)
    ofn.lpstrFile = ctypes.cast(file_buffer, ctypes.c_wchar_p)
    ofn.nMaxFile = MAX_PATH
    
    ofn.lpstrTitle = "Select Boshiamy (liu-uni.tab) Table File"
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST

    comdlg32 = ctypes.windll.comdlg32
    if comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
        return file_buffer.value
    return None

def main():
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    cinbase_dir = os.path.dirname(tools_dir)
    pime_python_dir = os.path.dirname(cinbase_dir)
    pime_root = os.path.dirname(pime_python_dir)
    
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
            "Shiamy (Liu) input method requires your licensed liu-uni.tab table file.\nWould you like to locate it now?",
            "PIME - Shiamy Setup",
            MB_OKCANCEL | MB_ICONQUESTION
        )
        if ret == IDOK:
            tab_file = browse_for_file()

    if not tab_file or not os.path.exists(tab_file):
        print("No liu-uni.tab file selected. Skipping Shiamy setup.")
        return

    # Convert tab to cin
    cin_dir = os.path.join(cinbase_dir, "cin")
    os.makedirs(cin_dir, exist_ok=True)
    out_cin = os.path.join(cin_dir, "liu.cin")
    
    unitab2cin = os.path.join(tools_dir, "liu_unitab2cin.py")
    cintojson = os.path.join(tools_dir, "cintojson.py")
    
    print(f"Converting {tab_file} to {out_cin}...")
    subprocess.call([python_exe, unitab2cin, tab_file, out_cin])
    
    if os.path.exists(out_cin):
        print("Converting liu.cin to JSON...")
        subprocess.call([python_exe, cintojson, "liu.cin"], cwd=tools_dir)
        ctypes.windll.user32.MessageBoxW(
            0,
            "Shiamy (Liu) table imported successfully!",
            "PIME - Shiamy Setup",
            0x40 # MB_ICONINFORMATION
        )
    else:
        ctypes.windll.user32.MessageBoxW(
            0,
            "Failed to convert liu-uni.tab file.",
            "PIME - Shiamy Setup",
            0x10 # MB_ICONSTOP
        )

if __name__ == '__main__':
    main()
