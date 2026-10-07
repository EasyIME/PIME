"""
Standalone Liu (Boshiamy) Table Importer Tool for PIME.
Allows the user to select their legally owned liu-uni.tab file,
converts it to liu.cin and then compiles it into JSON for PIME cinbase.
"""

import os
import sys
import subprocess
import ctypes

def browse_for_file():
    # Use PowerShell to show OpenFileDialog without external dependencies
    ps_cmd = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$f = New-Object System.Windows.Forms.OpenFileDialog; "
        "$f.Filter = 'liu-uni.tab (*.tab)|*.tab|All Files (*.*)|*.*'; "
        "$f.Title = 'Select Boshiamy (liu-uni.tab) Table File'; "
        "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $f.FileName }"
    )
    try:
        res = subprocess.check_output(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return res.strip()
    except Exception as e:
        print(f"File dialog failed: {e}")
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
