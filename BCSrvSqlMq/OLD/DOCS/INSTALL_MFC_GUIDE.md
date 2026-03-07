# Installing MFC Libraries for Visual Studio 2026

**Created:** 2026-02-27
**Purpose:** Fix build error MSB8041 - MFC libraries required for BCSrvSqlMq project

---

## Problem

When trying to build BCSrvSqlMq, you get this error:

```
error MSB8041: as bibliotecas MFC são necessárias para este projeto.
Instale-as usando o instalador do Visual Studio (guia Componentes Individuais)
para todas as arquiteturas e os conjuntos de ferramentas que estão sendo usados.
```

**Translation:** "MFC libraries are required for this project. Install them using the Visual Studio installer (Individual Components tab) for all architectures and toolsets being used."

---

## Solution: Install MFC Libraries

### Method 1: Using Visual Studio Installer (RECOMMENDED)

#### Step 1: Open Visual Studio Installer

**Option A - From Start Menu:**
1. Press Windows key
2. Type: `Visual Studio Installer`
3. Click on "Visual Studio Installer"

**Option B - From Visual Studio:**
1. Open Visual Studio 2026
2. Go to menu: **Tools** → **Get Tools and Features...**
3. Visual Studio Installer will open

**Option C - Direct Path:**
- Run: `"C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe"`

#### Step 2: Modify Visual Studio Installation

1. In Visual Studio Installer, find **Visual Studio Community 2026** (or Professional/Enterprise)
2. Click the **Modify** button (NOT "Update" or "Launch")
3. Wait for the installer to load the component list

#### Step 3: Install MFC Components

You'll see tabs at the top: **Workloads** | **Individual components** | **Language packs**

**Click on "Individual components" tab**

Now search and select these components:

##### For Win32 (32-bit) - REQUIRED:
Search for "MFC" and check these boxes:

- ☑ **C++ MFC for latest v143 build tools (x86 & x64)**
- ☑ **C++ ATL for latest v143 build tools (x86 & x64)**

OR if you see v180 (Visual Studio 2026 specific):
- ☑ **C++ MFC for latest v180 build tools (x86 & x64)**
- ☑ **C++ ATL for latest v180 build tools (x86 & x64)**

##### Additional Components (Recommended):
Also check these to ensure full MFC support:

- ☑ **MSVC v143 - VS 2022 C++ x64/x86 build tools (Latest)**
- ☑ **MSVC v143 - VS 2022 C++ x64/x86 Spectre-mitigated libs (Latest)**
- ☑ **Windows Universal CRT SDK**

**Search tip:** Type "MFC" in the search box at the top of the component list

#### Step 4: Review and Install

1. At the bottom right, you'll see:
   - Total download size
   - Total install size

2. Click **Modify** button (bottom right)

3. Click **Yes** on User Account Control prompt

4. Wait for installation to complete (may take 10-30 minutes depending on internet speed)

5. When done, you'll see "Installation succeeded!" message

6. Click **Close**

---

### Method 2: Using Visual Studio Installer Command Line

Open **Command Prompt as Administrator** and run:

```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe" ^
  modify ^
  --installPath "C:\Program Files\Microsoft Visual Studio\18\Community" ^
  --add Microsoft.VisualStudio.Component.VC.ATLMFC ^
  --add Microsoft.VisualStudio.Component.VC.ATLMFC.Spectre ^
  --passive
```

**Parameters:**
- `modify` - Modify existing installation
- `--installPath` - Path to VS installation
- `--add` - Component to add
- `--passive` - Show progress but no interaction required

---

## Verify Installation

After installing MFC, verify it's available:

### Check 1: Verify MFC Files Exist

Open Command Prompt and run:

```cmd
dir "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\*\atlmfc" /s
```

You should see folders like:
```
C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.50.35717\atlmfc
C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.44.35207\atlmfc
```

### Check 2: Look for MFC Header Files

```cmd
dir "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.50.35717\atlmfc\include\afx.h"
```

Should show the file exists.

### Check 3: Look for MFC Libraries

```cmd
dir "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.50.35717\atlmfc\lib\x86\mfc*.lib"
```

Should list MFC library files like: `mfc140.lib`, `mfcs140.lib`, etc.

---

## After Installing MFC: Rebuild BCSrvSqlMq

Once MFC is installed, rebuild the project:

### Option A: Using CMake (Recommended)

```cmd
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\BCSrvSqlMq"
cmake --build build --config Release
```

### Option B: Clean Rebuild

If the above fails, do a clean rebuild:

```cmd
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\BCSrvSqlMq"
rmdir /s /q build
cmake -S . -B build
cmake --build build --config Release
```

### Option C: Using Visual Studio IDE

1. Open Visual Studio 2026
2. File → Open → Project/Solution
3. Navigate to: `c:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\BCSrvSqlMq\build`
4. Open: `BCSrvSqlMq.sln`
5. Set configuration to **Release** (top toolbar)
6. Menu: **Build** → **Rebuild Solution**

---

## Expected Build Output

After successful build, you should see:

```
Build succeeded.
    0 Warning(s)
    0 Error(s)

Time Elapsed 00:00:30.45
```

And the executable will be at:
```
c:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\BCSrvSqlMq\build\Release\BCSrvSqlMq.exe
```

File size: ~228 KB (similar to original)

---

## Troubleshooting

### Problem: "Component not found in installer"

**Solution:** Your Visual Studio version might use different component names. Try:
1. In Individual Components, search for: `MFC`
2. Select ALL MFC-related components shown
3. Also select ALL ATL-related components

### Problem: "Installation failed"

**Solutions:**
1. Close Visual Studio completely before installing
2. Restart Visual Studio Installer
3. Try again
4. If still fails, restart computer and retry

### Problem: "Still getting MFC error after install"

**Solutions:**
1. Close Visual Studio
2. Delete build directory: `rmdir /s /q build`
3. Reconfigure: `cmake -S . -B build`
4. Build: `cmake --build build --config Release`

### Problem: "Wrong toolset version"

If CMake keeps using wrong toolset:

```cmd
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\BCSrvSqlMq"
rmdir /s /q build
cmake -S . -B build -G "Visual Studio 18 2026" -T "v143"
cmake --build build --config Release
```

The `-T "v143"` forces use of VS 2022 toolset which has MFC.

---

## Component IDs Reference

If using command-line installation, here are the component IDs:

```
Microsoft.VisualStudio.Component.VC.ATLMFC               - MFC and ATL support
Microsoft.VisualStudio.Component.VC.ATLMFC.Spectre      - MFC with Spectre mitigations
Microsoft.VisualStudio.Component.VC.143.ATL              - VS 2022 ATL
Microsoft.VisualStudio.Component.VC.143.MFC              - VS 2022 MFC
Microsoft.VisualStudio.Component.VC.143.ATL.Spectre     - VS 2022 ATL (Spectre)
Microsoft.VisualStudio.Component.VC.143.MFC.Spectre     - VS 2022 MFC (Spectre)
```

---

## Next Steps After Successful Build

Once the build succeeds:

1. **Copy the new executable:**
   ```cmd
   copy "c:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\BCSrvSqlMq\build\Release\BCSrvSqlMq.exe" ^
        "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release\"
   ```

2. **Test in console mode:**
   ```cmd
   cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"
   BCSrvSqlMq.exe -d
   ```

3. **Verify no error 2043:**
   - Look for: "Task RmtReq Iniciada", "Task RmtRsp Iniciada", etc.
   - Should NOT see: "8019 E MQOPEN ended with reason code 2043"
   - All 8 threads should stay running

4. **Install as service:**
   ```cmd
   net stop BCSrvSqlMq
   copy BCSrvSqlMq.exe "C:\BCSrvSqlMq\BCSrvSqlMq.exe" /Y
   net start BCSrvSqlMq
   ```

---

## Summary

**What to do:**
1. Open Visual Studio Installer
2. Click "Modify" on VS 2026
3. Go to "Individual components" tab
4. Search and select MFC components
5. Click "Modify" to install
6. Wait for installation (10-30 minutes)
7. Rebuild BCSrvSqlMq project
8. Test the service

**Estimated time:** 30-45 minutes (mostly download/install)

---

**Need Help?**
- If you encounter issues during installation, check the Visual Studio installation logs at:
  - `%TEMP%\dd_setup_*.log`
  - `%TEMP%\dd_installer_*.log`

**Last Updated:** 2026-02-27 12:00 PM
