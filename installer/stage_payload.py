import os
import sys
import shutil
import json
import zipfile
import py_compile
import compileall

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    stage_dir = os.path.join(repo_root, "build", "stage")
    
    if os.path.exists(stage_dir):
        shutil.rmtree(stage_dir)
    os.makedirs(stage_dir)
    
    # 1. Copy python/ and node/
    print("Copying python and node...")
    shutil.copytree(os.path.join(repo_root, "python"), os.path.join(stage_dir, "python"))
    shutil.copytree(os.path.join(repo_root, "node"), os.path.join(stage_dir, "node"))
    
    # 2. Minify cinbase/json/*.json
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
                    
    # 3. Store python3*.zip uncompressed
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
                    zout.writestr(item, zin.read(item.filename))
            os.replace(temp_zip, zip_path)
        
    # 4. Exclude dev files
    print("Excluding dev files...")
    exclude_exts = [".map"]
    exclude_files = ["python.cat"]
    for root, dirs, files in os.walk(stage_dir):
        for file in files:
            if any(file.endswith(ext) for ext in exclude_exts) or file in exclude_files:
                os.remove(os.path.join(root, file))
                
    # 5. Precompile Python bytecode
    print("Precompiling Python bytecode...")
    compileall.compile_dir(os.path.join(stage_dir, "python"), force=True, invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH, quiet=1)

    print("Staging complete.")

if __name__ == "__main__":
    main()
