# VS Code Development Guide for SPB Monorepo

Complete guide for working with all SPB projects in Visual Studio Code.

---

## Quick Start

### 1. Open the Workspace

**Double-click** `SPB-Workspace.code-workspace` or run:

```bash
code SPB-Workspace.code-workspace
```

This will open all 4 projects + root folder in a multi-root workspace with:
- 📦 spb-shared (Models)
- 🌐 SPBSite (Web)
- 🔌 BCSrvSqlMq (MQ Service)
- 📊 Carga_Mensageria (ETL)
- 📁 Root (for git operations and docs)

---

## Setup Python Environments

### Option A: Shared Virtual Environment (Simpler)

Create one venv at the root and use it for all projects:

```bash
# At root (Novo_SPB/)
python -m venv venv
source venv/Scripts/activate  # or venv\Scripts\activate on Windows

# Install all dependencies
pip install -e spb-shared
cd spbsite && pip install -r requirements.txt && cd ..
cd BCSrvSqlMq/python && pip install -r requirements.txt && cd ../..
```

### Option B: Separate Virtual Environments (Isolated)

Create separate venv for each project:

```bash
# spb-shared
cd spb-shared
python -m venv venv
source venv/Scripts/activate
pip install -e .
deactivate

# spbsite
cd ../spbsite
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
pip install -e ../spb-shared
deactivate

# BCSrvSqlMq
cd ../BCSrvSqlMq/python
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
pip install -e ../../spb-shared
deactivate
```

Then select the appropriate interpreter for each project in VS Code:
- `Ctrl+Shift+P` → "Python: Select Interpreter"
- Choose the venv for the current project folder

---

## Working with Projects

### Switching Between Projects

Use the **Explorer** panel (`Ctrl+Shift+E`):
- Each project appears as a separate root folder
- Click on the folder name to expand/navigate
- Files from all projects are searchable

### Opening Files Across Projects

**Quick Open** (`Ctrl+P`):
```
# Type filename - VS Code searches all workspace folders
models.py           # Shows models from all projects
database.py         # Shows database configs from all projects

# Use folder prefix to be specific
spb-shared/         # Shows files only from spb-shared
spbsite/app/        # Shows files from spbsite/app/
```

### Running Projects

#### SPBSite (Web Server)

**Method 1: Debug Configuration** (Recommended)
1. Go to **Run and Debug** (`Ctrl+Shift+D`)
2. Select "SPBSite: Run Server"
3. Press `F5`

**Method 2: Terminal**
```bash
cd spbsite
uvicorn app.main:app --reload --port 8000
```

**Method 3: Tasks**
1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. Select "Run SPBSite"

**Access:** http://localhost:8000

---

#### BCSrvSqlMq (MQ Service)

**Method 1: Debug Configuration**
1. Go to **Run and Debug** (`Ctrl+Shift+D`)
2. Select "BCSrvSqlMq: Run Service"
3. Press `F5`

**Method 2: Terminal**
```bash
cd BCSrvSqlMq/python
python -m bcsrvsqlmq.main_srv
```

**Method 3: Tasks**
1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. Select "Run BCSrvSqlMq"

---

#### Carga_Mensageria (ETL Tool)

**Method 1: Debug Configuration**
1. Go to **Run and Debug** (`Ctrl+Shift+D`)
2. Select "Carga_Mensageria: Run GUI"
3. Press `F5`

**Method 2: Terminal**
```bash
cd Carga_Mensageria
python main.py
```

---

### Running Tests

**SPBSite Tests:**

**Method 1: Debug Configuration**
1. Go to **Run and Debug** (`Ctrl+Shift+D`)
2. Select "SPBSite: Run Tests"
3. Press `F5`

**Method 2: Testing Panel**
1. Open **Testing** view (`Ctrl+Shift+Y` or beaker icon)
2. Click "Configure Python Tests" → pytest
3. Run tests from the panel

**Method 3: Terminal**
```bash
cd spbsite
pytest tests/ -v
```

---

## Database Operations

### Seeding SPBSite Database

**Method 1: Debug Configuration**
1. Go to **Run and Debug** (`Ctrl+Shift+D`)
2. Select "SPBSite: Seed Database"
3. Press `F5`

**Method 2: Terminal**
```bash
cd spbsite
python -m app.seed
```

### Alembic Migrations

**Create Migration:**
```bash
cd spb-shared
alembic revision --autogenerate -m "Description"
```

**Or use Task:**
1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. Select "Create Alembic Migration"
3. Enter migration message

**Apply Migrations:**
```bash
# spb-shared
cd spb-shared
alembic upgrade head

# spbsite
cd spbsite
alembic upgrade head
```

---

## Git Operations

### Using the Workspace

The workspace includes the root folder for git operations:

**Source Control Panel** (`Ctrl+Shift+G`):
- Shows changes across all projects
- Can commit from any project
- Handles the monorepo structure

**Common Git Commands:**

```bash
# Check status
git status

# Stage changes
git add PROJECTS_OVERVIEW.md
git add spbsite/app/main.py
git add BCSrvSqlMq/python/bcsrvsqlmq/

# Commit
git commit -m "Your message"

# Push
git push
```

**GitLens Extension:**
- View file history: Right-click file → "GitLens: Open File History"
- Blame: Click line → see commit info in status bar
- Compare: Right-click → "GitLens: Compare with..."

---

## Useful VS Code Features

### 1. Multi-Cursor Editing

- `Alt+Click` - Add cursor
- `Ctrl+Alt+Down/Up` - Add cursor below/above
- `Ctrl+D` - Select next occurrence
- `Ctrl+Shift+L` - Select all occurrences

### 2. Search Across Projects

**Find in Files** (`Ctrl+Shift+F`):
```
Search: SPBControle
Filter: spb-shared/**/*.py
```

**Find and Replace Across Projects:**
1. `Ctrl+Shift+H`
2. Search for text
3. Replace in specific folders or all

### 3. Integrated Terminal

**Open Terminal** (`Ctrl+`backtick`):

**Multiple Terminals:**
1. `Ctrl+Shift+`backtick`` - New terminal
2. Use dropdown to switch between terminals
3. Right-click folder → "Open in Integrated Terminal" (opens at that folder)

**Split Terminal:**
- `Ctrl+Shift+5` - Split terminal

### 4. Breadcrumbs Navigation

**Navigate file structure:**
- Click breadcrumb at top of editor
- `Ctrl+Shift+.` - Focus breadcrumbs

### 5. Peek Definition

- `Alt+F12` - Peek definition (inline view)
- `F12` - Go to definition
- `Ctrl+Click` - Go to definition

**Example:** In SPBSite, `Alt+F12` on `SPBControle` will show the model definition from spb-shared inline.

### 6. Symbol Search

**Go to Symbol in Workspace** (`Ctrl+T`):
```
Type: SPBControle
```
Shows all symbols named SPBControle across all projects.

### 7. Refactoring

- `F2` - Rename symbol (across all files)
- `Ctrl+Shift+R` - Refactor menu

---

## Recommended Extensions

The workspace suggests these extensions:

### Essential
1. **Python** (ms-python.python) - Python support
2. **Pylance** (ms-python.vscode-pylance) - IntelliSense
3. **Black Formatter** (ms-python.black-formatter) - Code formatting
4. **Ruff** (charliermarsh.ruff) - Fast linting

### Helpful
5. **XML** (redhat.vscode-xml) - XML/XSL support
6. **IntelliCode** (visualstudioexptteam.vscodeintellicode) - AI-assisted completions
7. **GitLens** (eamodio.gitlens) - Enhanced git features
8. **Git History** (donjayamanne.githistory) - View git log/history

### Install All Recommended Extensions

When you open the workspace, VS Code will prompt:
> "This workspace has extension recommendations"

Click **Install All** or:
1. `Ctrl+Shift+X` → Extensions
2. Type `@recommended`
3. Install workspace recommendations

---

## Keyboard Shortcuts Cheat Sheet

| Action | Shortcut |
|--------|----------|
| Quick Open | `Ctrl+P` |
| Command Palette | `Ctrl+Shift+P` |
| Explorer | `Ctrl+Shift+E` |
| Search | `Ctrl+Shift+F` |
| Source Control | `Ctrl+Shift+G` |
| Debug | `Ctrl+Shift+D` |
| Extensions | `Ctrl+Shift+X` |
| Terminal | `Ctrl+`backtick` |
| New Terminal | `Ctrl+Shift+`backtick` |
| Find in File | `Ctrl+F` |
| Replace in File | `Ctrl+H` |
| Go to Definition | `F12` |
| Peek Definition | `Alt+F12` |
| Go to Symbol | `Ctrl+T` |
| Rename Symbol | `F2` |
| Format Document | `Shift+Alt+F` |
| Run/Debug | `F5` |
| Toggle Breakpoint | `F9` |
| Step Over | `F10` |
| Step Into | `F11` |

---

## Debugging

### Setting Breakpoints

1. Click in the gutter (left of line numbers) - Red dot appears
2. Or press `F9` on the line

### Debug Configurations Available

1. **SPBSite: Run Server** - Debug web server
2. **SPBSite: Seed Database** - Debug seeding
3. **SPBSite: Run Tests** - Debug tests
4. **BCSrvSqlMq: Run Service** - Debug MQ service
5. **Carga_Mensageria: Run GUI** - Debug ETL tool

### Debug Workflow

1. Set breakpoints in code
2. `Ctrl+Shift+D` → Select configuration
3. `F5` to start debugging
4. Use debug controls:
   - `F10` - Step over
   - `F11` - Step into
   - `Shift+F11` - Step out
   - `F5` - Continue

### Debug Console

While debugging:
- **Variables** panel - Inspect variables
- **Watch** panel - Add expressions to watch
- **Call Stack** - View execution stack
- **Debug Console** - Execute code in context

---

## Project-Specific Tips

### spb-shared

**Editing Models:**
1. Edit model in `spb_shared/models/`
2. Create migration: Task → "Create Alembic Migration"
3. Apply to all projects:
   ```bash
   cd spb-shared && alembic upgrade head
   cd ../spbsite && alembic upgrade head
   cd ../BCSrvSqlMq && alembic upgrade head
   ```

**IntelliSense for Models:**
- Type hints work automatically
- `Ctrl+Space` for autocomplete
- Hover over types for info

### SPBSite

**Route Development:**
1. Edit router in `app/routers/`
2. Save (auto-reload enabled)
3. Test at http://localhost:8000
4. Check logs in integrated terminal

**Template Editing:**
1. Edit Jinja2 templates in `app/templates/`
2. Refresh browser to see changes
3. Install "Jinja" extension for syntax highlighting

**Static Files:**
- `app/static/` - CSS, JS, images
- Auto-served at `/static/` URL

### BCSrvSqlMq

**IBM MQ Development:**
1. Ensure IBM MQ is running
2. Check `BCSrvSqlMq.ini` configuration
3. Debug with breakpoints in handlers
4. Monitor logs in terminal

**Database Operations:**
- Uses same models as SPBSite via spb-shared
- Test queries in Debug Console

### Carga_Mensageria

**ETL Development:**
1. Edit steps in `etapas.py`
2. Run GUI to test
3. Check `BCSPBSTR.db` for results
4. Use SQLite extension to view database

---

## Common Workflows

### 1. Add New Feature to SPBSite

```bash
# 1. Create feature branch
git checkout -b feature/new-message-type

# 2. Edit model if needed (spb-shared)
# Edit spb-shared/spb_shared/models/messages.py

# 3. Create migration
cd spb-shared
alembic revision --autogenerate -m "Add new message type"
alembic upgrade head

# 4. Apply to SPBSite
cd ../spbsite
alembic upgrade head

# 5. Implement feature in SPBSite
# Edit app/routers/, app/services/, app/templates/

# 6. Test
pytest tests/ -v

# 7. Commit
git add .
git commit -m "Add new message type feature"
```

### 2. Fix Bug in BCSrvSqlMq

```bash
# 1. Reproduce issue with debugger
# Set breakpoints in BCSrvSqlMq/python/bcsrvsqlmq/

# 2. Run with debugger (F5)
# Step through code to find issue

# 3. Fix code
# Edit relevant .py files

# 4. Test fix
# Re-run with debugger

# 5. Commit
git add BCSrvSqlMq/python/
git commit -m "Fix message acknowledgment bug"
```

### 3. Update Shared Model

```bash
# 1. Edit model
# Edit spb-shared/spb_shared/models/

# 2. Create migration
cd spb-shared
alembic revision --autogenerate -m "Update SPBControle fields"
alembic upgrade head

# 3. Apply to all projects
cd ../spbsite && alembic upgrade head
cd ../BCSrvSqlMq && alembic upgrade head

# 4. Update code in affected projects
# Check where model is used with Ctrl+Shift+F

# 5. Test all projects
# Run SPBSite tests
# Test BCSrvSqlMq manually

# 6. Commit
git add spb-shared/ spbsite/ BCSrvSqlMq/
git commit -m "Update SPBControle model with new fields"
```

---

## Troubleshooting

### Python Interpreter Not Found

1. `Ctrl+Shift+P` → "Python: Select Interpreter"
2. Choose correct venv
3. Or create new venv: `python -m venv venv`

### Import Errors (spb-shared not found)

```bash
# Install spb-shared in editable mode
pip install -e path/to/spb-shared

# Or from each project:
cd spbsite
pip install -e ../spb-shared
```

### Auto-reload Not Working (SPBSite)

- Check if `--reload` flag is present in launch config
- Restart the debug session
- Check file permissions

### Breakpoints Not Hit

- Ensure "justMyCode": false in launch config
- Check if code is actually executed
- Try adding `import pdb; pdb.set_trace()` instead

### Terminal Won't Activate venv

**Windows:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then restart VS Code.

---

## Alternative: Work on Individual Projects

If you prefer to work on one project at a time:

### Open Single Project

```bash
# Open just spbsite
cd spbsite
code .

# Open just BCSrvSqlMq
cd BCSrvSqlMq
code .
```

### Configure Python Path

Create `.vscode/settings.json` in each project:

```json
{
  "python.analysis.extraPaths": [
    "../spb-shared"
  ]
}
```

---

## Summary

**Best Practices:**
1. ✅ Use the **workspace file** for multi-project development
2. ✅ Install **spb-shared** in editable mode (`pip install -e`)
3. ✅ Use **debug configurations** instead of manual terminal commands
4. ✅ Use **tasks** for repetitive operations
5. ✅ Leverage **IntelliSense** and **go-to-definition** across projects
6. ✅ Use **integrated terminal** for all command-line operations
7. ✅ Enable **format on save** for consistent code style
8. ✅ Use **GitLens** for better git integration

**Happy Coding!** 🚀
