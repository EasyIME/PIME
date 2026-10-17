import glob
import json
import os
import py_compile
import compileall
import shutil
import stat
import subprocess
import time
import zipfile

def remove_dir(path):
    if not os.path.exists(path):
        return
    if os.name == 'nt':
        try:
            subprocess.run(["cmd.exe", "/c", "rd", "/s", "/q", os.path.normpath(path)], check=True, capture_output=True)
            if not os.path.exists(path):
                return
        except Exception:
            pass

    def on_error(func, p, exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            pass

    for _ in range(5):
        try:
            shutil.rmtree(path, onerror=on_error)
            if not os.path.exists(path):
                return
        except OSError:
            time.sleep(0.2)

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    stage_dir = os.path.join(repo_root, "build", "stage")
    
    if os.path.exists(stage_dir):
        remove_dir(stage_dir)
    os.makedirs(stage_dir)
    
    # 1. Copy python/ and node/
    print("Copying python and node...")
    shutil.copytree(
        os.path.join(repo_root, "python"),
        os.path.join(stage_dir, "python"),
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc")
    )
    shutil.copytree(
        os.path.join(repo_root, "node"),
        os.path.join(stage_dir, "node"),
        ignore=shutil.ignore_patterns(".git", "node_modules")
    )
    
    # 2. Stage Rime data from brise submodule and opencc
    print("Staging Rime data...")
    rime_dir = os.path.join(stage_dir, "python", "input_methods", "rime")
    rime_brise = os.path.join(repo_root, "python", "input_methods", "rime", "brise")
    rime_data = os.path.join(rime_dir, "data")
    rime_opencc = os.path.join(rime_data, "opencc")
    os.makedirs(rime_data, exist_ok=True)
    os.makedirs(rime_opencc, exist_ok=True)

    if os.path.exists(rime_brise):
        for pattern in ["*.txt", "*.yaml"]:
            for f in glob.glob(os.path.join(rime_brise, pattern)):
                shutil.copy2(f, rime_data)
        for subdir in ["preset", "supplement", "extra"]:
            subpath = os.path.join(rime_brise, subdir)
            if os.path.exists(subpath):
                for f in glob.glob(os.path.join(subpath, "*.yaml")):
                    shutil.copy2(f, rime_data)

    opencc_src = os.path.join(repo_root, "python", "opencc")
    if os.path.exists(opencc_src):
        for pattern in ["*.json", "*.ocd"]:
            for f in glob.glob(os.path.join(opencc_src, pattern)):
                shutil.copy2(f, rime_opencc)

    # Remove raw brise submodule directory from staged rime
    staged_brise = os.path.join(rime_dir, "brise")
    if os.path.exists(staged_brise):
        remove_dir(staged_brise)

    # 3. Stage bundled emojime and clean up input_methods build artifacts
    emojime_stage = os.path.join(stage_dir, "node", "input_methods", "emojime")
    emojime_dist = os.path.join(emojime_stage, "dist", "index.js")
    if os.path.exists(emojime_dist):
        shutil.copy2(emojime_dist, os.path.join(emojime_stage, "index.js"))
        remove_dir(os.path.join(emojime_stage, "dist"))
        remove_dir(os.path.join(emojime_stage, "src"))

    im_dir = os.path.join(stage_dir, "node", "input_methods")
    if os.path.exists(im_dir):
        for im in os.listdir(im_dir):
            im_nm = os.path.join(im_dir, im, "node_modules")
            if os.path.exists(im_nm):
                remove_dir(im_nm)

    # 4. Minify cinbase/json/*.json
    print("Minifying JSON...")
    json_dir = os.path.join(stage_dir, "python", "cinbase", "json")
    if os.path.exists(json_dir):
        for f in os.listdir(json_dir):
            if f.endswith(".json"):
                fpath = os.path.join(json_dir, f)
                with open(fpath, "r", encoding="utf-8") as file:
                    data = json.load(file)
                with open(fpath, "w", encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, separators=(',', ':'))
                    
    # 4. Store python3*.zip uncompressed
    print("Re-storing python zip uncompressed...")
    py_dir = os.path.join(stage_dir, "python", "python3")
    if os.path.exists(py_dir):
        zip_path = None
        for f in os.listdir(py_dir):
            if f.startswith("python") and f.endswith(".zip"):
                zip_path = os.path.join(py_dir, f)
                break
                
        if zip_path:
            temp_zip = zip_path + ".tmp"
            with zipfile.ZipFile(zip_path, 'r') as zin, zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_STORED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    item.compress_type = zipfile.ZIP_STORED
                    zout.writestr(item, data)
            os.replace(temp_zip, zip_path)
        
    # 5. Exclude dev files
    print("Excluding dev files...")
    exclude_exts = [".map"]
    exclude_files = ["python.cat"]
    for root, dirs, files in os.walk(stage_dir):
        for file in files:
            if any(file.endswith(ext) for ext in exclude_exts) or file in exclude_files:
                os.remove(os.path.join(root, file))
                
    # 6. Precompile Python bytecode
    print("Precompiling Python bytecode...")
    python_stage = os.path.join(stage_dir, "python")
    compileall.compile_dir(
        python_stage,
        force=True,
        invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
        stripdir=python_stage,
        quiet=1
    )

    print("Staging complete.")

if __name__ == "__main__":
    main()
