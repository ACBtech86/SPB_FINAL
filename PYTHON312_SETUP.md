# Python 3.12 Setup for pymqi

This guide shows how to install and use Python 3.12 alongside Python 3.13 to enable `pymqi` installation.

---

## Why Python 3.12?

- **Python 3.13** is too new for `pymqi` (released August 2025)
- **Python 3.12** is fully compatible with `pymqi`
- You can keep both versions installed side-by-side

---

## Step 1: Download Python 3.12

1. Go to https://www.python.org/downloads/
2. Click "Download Python 3.12.x" (latest 3.12 version)
3. **Important:** During installation:
   - ✅ Check "Add Python 3.12 to PATH"
   - ✅ Check "Install for all users" (optional)
   - Choose "Customize installation"
   - ✅ Check "py launcher"
   - ✅ Check "Add Python to environment variables"

---

## Step 2: Verify Installation

After installing, verify both Python versions are available:

```bash
# Check Python 3.13 (current)
python --version
# Should show: Python 3.13.7

# Check Python 3.12 (new)
py -3.12 --version
# Should show: Python 3.12.x

# Or
python3.12 --version
```

---

## Step 3: Create Virtual Environment with Python 3.12

### For spb-shared

```bash
cd spb-shared
py -3.12 -m venv venv312
venv312\Scripts\activate
pip install -e .
```

### For SPBSite

```bash
cd spbsite
py -3.12 -m venv venv312
venv312\Scripts\activate
pip install -r requirements.txt
pip install -e ../spb-shared
```

### For BCSrvSqlMq

```bash
cd BCSrvSqlMq/python
py -3.12 -m venv venv312
venv312\Scripts\activate
pip install -r requirements.txt
pip install -e ../../spb-shared

# NOW install pymqi (should work!)
pip install pymqi
```

---

## Step 4: Install pymqi with Python 3.12

```bash
# Activate the 3.12 virtual environment
cd BCSrvSqlMq/python
venv312\Scripts\activate

# Install pymqi
pip install pymqi

# Test it
python -c "import pymqi; print('pymqi version:', pymqi.__version__)"
```

---

## Step 5: Update VS Code Settings

Update the workspace file to use Python 3.12:

**SPB-Workspace.code-workspace:**

```json
{
  "folders": [
    {
      "name": "📦 spb-shared (Models)",
      "path": "spb-shared"
    },
    {
      "name": "🌐 SPBSite (Web)",
      "path": "spbsite"
    },
    {
      "name": "🔌 BCSrvSqlMq (MQ Service)",
      "path": "BCSrvSqlMq"
    }
  ],
  "settings": {
    "python.defaultInterpreterPath": "${workspaceFolder}/venv312/Scripts/python.exe",
    "python.terminal.activateEnvironment": true
  }
}
```

Or select interpreter manually in VS Code:
1. `Ctrl+Shift+P`
2. "Python: Select Interpreter"
3. Choose `venv312/Scripts/python.exe` for each folder

---

## Step 6: Run Tests with Python 3.12

### Check MQ Status

```bash
cd BCSrvSqlMq/python
venv312\Scripts\activate
cd ../..
python test_scripts/check_mq_status.py
```

### Browse MQ Queues

```bash
python test_scripts/browse_mq_queue.py QR.REQ.36266751.00038166.01
```

### Simulate BACEN Response

```bash
python test_scripts/simulate_bacen_response.py -o 20260307120000 -t COA
```

---

## Running Projects with Python 3.12

### SPBSite

```bash
cd spbsite
venv312\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### BCSrvSqlMq

```bash
cd BCSrvSqlMq/python
venv312\Scripts\activate
python -m bcsrvsqlmq.main_srv
```

---

## Python Version Comparison

| Feature | Python 3.13 | Python 3.12 |
|---------|-------------|-------------|
| SPBSite | ✅ Works | ✅ Works |
| BCSrvSqlMq | ✅ Works | ✅ Works |
| spb-shared | ✅ Works | ✅ Works |
| **pymqi** | ❌ Won't compile | ✅ **Works!** |
| simple_db_test.py | ✅ Works | ✅ Works |
| Full MQ testing | ❌ No | ✅ **Yes!** |

---

## Quick Commands Reference

### Switch to Python 3.12

```bash
# Create venv with 3.12
py -3.12 -m venv venv312

# Activate it
venv312\Scripts\activate

# Check version
python --version  # Should show 3.12.x
```

### Switch Back to Python 3.13

```bash
# Deactivate current venv
deactivate

# Create/activate 3.13 venv
python -m venv venv
venv\Scripts\activate

# Check version
python --version  # Should show 3.13.7
```

---

## Keeping Both Versions

You can maintain separate virtual environments:

```
spbsite/
├── venv/           # Python 3.13 (original)
├── venv312/        # Python 3.12 (for pymqi)

BCSrvSqlMq/python/
├── venv/           # Python 3.13 (original)
├── venv312/        # Python 3.12 (for pymqi)
```

Use Python 3.12 only when you need pymqi features!

---

## Troubleshooting

### "py: command not found"

The Python Launcher (`py`) might not be installed. Use direct path:

```bash
"C:\Users\AntonioBosco\AppData\Local\Programs\Python\Python312\python.exe" -m venv venv312
```

### pymqi Still Won't Install

Make sure:
1. Visual Studio 2022 is installed
2. You're using Python 3.12 (not 3.13)
3. Virtual environment is activated
4. Try:
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install pymqi
   ```

### Import Error

```bash
# Make sure you're in the right venv
which python
# Should show path with venv312

# Reinstall pymqi
pip uninstall pymqi
pip install pymqi
```

---

## Alternative: Use Python 3.12 as Default

If you want Python 3.12 as your main Python:

1. Uninstall Python 3.13 (optional)
2. Install Python 3.12
3. Recreate all virtual environments
4. No need for `py -3.12` prefix

---

## Summary

✅ **Install Python 3.12** from python.org
✅ **Create venv312** in each project
✅ **Install pymqi** in BCSrvSqlMq venv312
✅ **Run MQ test scripts** with Python 3.12
✅ **Keep Python 3.13** for other work

Python 3.12 unlocks full pymqi functionality for complete E2E testing! 🚀
