import os
import shutil
import subprocess
import sys

def main():
    installer_dir = os.path.dirname(os.path.abspath(__file__))
    release_dir = os.path.join(installer_dir, "PIME_Core", "bin", "x86", "Release")
    zhtw_msi = os.path.join(release_dir, "zh-TW", "PIME_Core.msi")
    en_msi = os.path.join(release_dir, "en-US", "PIME_Core.msi")
    zhcn_msi = os.path.join(release_dir, "zh-CN", "PIME_Core.msi")

    wix_dll = os.path.expanduser(r"~/.nuget/packages/wixtoolset.sdk/4.0.6/tools/net6.0/wix.dll")
    wisubstg = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x86\wisubstg.vbs"
    wilangid = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x86\wilangid.vbs"

    en_mst = os.path.join(release_dir, "en-US.mst")
    zhcn_mst = os.path.join(release_dir, "zh-CN.mst")

    print("1. Generating language transforms (base is zh-TW)...")
    subprocess.check_call(["dotnet", wix_dll, "msi", "transform", "-t", "language", zhtw_msi, en_msi, "-o", en_mst])
    subprocess.check_call(["dotnet", wix_dll, "msi", "transform", "-t", "language", zhtw_msi, zhcn_msi, "-o", zhcn_mst])

    print(f"en-US.mst size: {os.path.getsize(en_mst)} bytes")
    print(f"zh-CN.mst size: {os.path.getsize(zhcn_mst)} bytes")

    output_msi = os.path.join(release_dir, "PIME_Core.msi")
    print(f"2. Creating monolithic base MSI from zh-TW: {output_msi}")
    shutil.copy2(zhtw_msi, output_msi)

    print("3. Embedding transforms into MSI substorages...")
    # First remove existing substorages if any
    subprocess.run(["cscript", "//nologo", wisubstg, output_msi, "/D", "1033"], capture_output=True)
    subprocess.run(["cscript", "//nologo", wisubstg, output_msi, "/D", "2052"], capture_output=True)

    # Embed 1033 and 2052
    subprocess.check_call(["cscript", "//nologo", wisubstg, output_msi, en_mst, "1033"])
    subprocess.check_call(["cscript", "//nologo", wisubstg, output_msi, zhcn_mst, "2052"])

    print("4. Updating Template summary to include all languages...")
    subprocess.check_call(["cscript", "//nologo", wilangid, output_msi, "Package", "1028,1033,2052"])

    # Clean up intermediate transforms
    print("5. Cleaning up intermediate transform files...")
    if os.path.exists(en_mst):
        os.remove(en_mst)
    if os.path.exists(zhcn_mst):
        os.remove(zhcn_mst)

    final_size = os.path.getsize(output_msi)
    print(f"\nSUCCESS! Monolithic multi-language MSI created:")
    print(f"Path: {output_msi}")
    print(f"Size: {final_size} bytes ({final_size / (1024*1024):.2f} MB)")

    print("\nListing substorages inside MSI:")
    res = subprocess.run(["cscript", "//nologo", wisubstg, output_msi], capture_output=True, text=True)
    print(res.stdout)

if __name__ == "__main__":
    main()
