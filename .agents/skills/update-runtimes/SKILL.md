---
name: update-runtimes
description: >-
  Use this skill when updating Python, Node.js, or their dependencies and
  packages in the PIME repository to the latest stable versions.
---

# Update Embedded Runtimes (Python & Node.js)

Runbook for updating the embedded 32-bit (x86) Windows Python and Node.js runtimes in PIME.

---

## Architecture & Layout

- **Python (`python/python3/`)**:
  - Base: 32-bit Windows embeddable package from [Python Releases for Windows](https://www.python.org/downloads/windows/).
  - `python3*._pth`: Has `import site` uncommented (saved as UTF-8 without BOM) so `site.main()` loads automatically.
  - **`Lib/site-packages/`**:
    - Houses non-builtin packages (`tornado`) and path configuration files (`*.pth`).
    - Relative paths in `.pth` files are evaluated relative to `Lib/site-packages/` (e.g. `../../..` reaches `python/`).
    - The update script automatically backs up and preserves all custom `*.pth` files and `requirements.txt` across upgrades.
  - `python/python3/requirements.txt`: Tracks required external Python packages.
  - PIME native modules (`opencc`, `libchewing`, `cinbase`) remain under `python/`.
- **Node.js (`node/`)**:
  - Base: 32-bit `node.exe` from [Node.js Distributions](https://nodejs.org/dist/).
  - `node/node_modules/`: Production dependencies from `node/package.json`.

---

## Procedure

### 1. Check Latest Versions & Package Safety
- Identify the latest stable:
  - Python 32-bit embeddable release (e.g., `3.12.9`).
  - Node.js 32-bit LTS/Current release (e.g., `22.14.0`).
- Check `node/package.json` and `python/python3/requirements.txt`. Warn if any package is deprecated or obsolete, and suggest modern replacements.

### 2. Run Update Script
Execute [update_runtimes.ps1](./scripts/update_runtimes.ps1) (handles downloading, pathing, dependencies, and cache cleanup):
```powershell
powershell -ExecutionPolicy Bypass -File .\.agents\skills\update-runtimes\scripts\update_runtimes.ps1 -NodeVersion "22.14.0" -PythonVersion "3.12.9"
```

### 3. Verify Runtimes
```powershell
# Verify Python & Tornado in site-packages
& .\python\python3\python.exe -c "import sys, tornado; print('Python:', sys.version); print('Tornado:', tornado.__file__)"

# Verify PIME backend services
& .\python\python3\python.exe -c "import server, serviceManager; print('PIME backend loaded!')"

# Verify Node.js
& .\node\node.exe -v
```

### 4. Git Review & Commit
The script automatically stages `node/` and `python/` via `git add -A` (adding new runtime files, staging modifications, and `git rm`-ing deleted obsolete files from older versions).

Review staged changes:
```powershell
git status
```
Ensure only expected runtime changes are staged and no `__pycache__` or `.pyc` files exist, then commit.
