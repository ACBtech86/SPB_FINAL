# BCSrvSqlMq - Quick Start Guide

**Resume on another machine:** Start here!

---

## 📍 Current Status

**Problem:** Service runs but all IBM MQ queues fail with error 2043
**Last Action:** About to test console mode
**Location:** `c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq`

---

## ⚡ IMMEDIATE ACTION (Do This First)

Open **Command Prompt as Administrator** and run:

```cmd
net stop BCSrvSqlMq
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"
BCSrvSqlMq.exe -d
```

**Watch what happens!**

---

## 🎯 What to Expect

### If Console Mode WORKS (no error 2043)
✅ The service code is fine!
✅ Problem is just the service account

**Solution:**
```cmd
# Run as Administrator
change_service_user.bat
# Enter MUSR_MQADMIN password when prompted
```

### If Console Mode FAILS (still error 2043)
❌ Deeper issue exists

**Solution:** Check `CONVERSATION_SUMMARY.md` for full details and enable MQ tracing

---

## 📋 What We've Already Fixed

1. ✅ Created 8 missing IBM MQ queues
2. ✅ Disabled ALL MQ security (CHLAUTH, CONNAUTH, AUTHOREV)
3. ✅ Added SYSTEM to mqm group
4. ✅ Set QM.61377677.01 as default Queue Manager
5. ✅ Configured Windows Registry with all settings

**Still getting error 2043!** → Testing console mode to determine if it's a service account issue.

---

## 🗂️ Key Files & Locations

### Project
- **Root:** `c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq`
- **Executable:** `build\Release\BCSrvSqlMq.exe`
- **Logs:** `C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log`

### Important Scripts (in build\Release)
- `debug_run.bat` - Run in console mode
- `change_service_user.bat` - Change to MUSR_MQADMIN
- `restart_service.bat` - Restart Windows Service
- `configure_registry.bat` - Configure registry (already done)

### Documentation
- `CONVERSATION_SUMMARY.md` - **Full details of everything**
- `ALTERNATIVE_SOLUTIONS.txt` - Other approaches to try
- `TESTING_GUIDE.md` - Complete testing procedures

---

## 🔧 System Info

- **OS:** Windows 11 Pro
- **PostgreSQL:** 18.1 (database: bcspbstr)
- **IBM MQ:** 9.4.5.0 (QM: QM.61377677.01)
- **Service:** BCSrvSqlMq (runs as LocalSystem)

---

## 🚨 Quick Troubleshooting

### Check if Service is Running
```cmd
sc query BCSrvSqlMq
```

### Check if Queue Manager is Running
```cmd
dspmq
```

### View Latest Logs
```cmd
type "C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log" | more
```

### Check Registry Config
```cmd
reg query "HKLM\SYSTEM\CurrentControlSet\Services\BCSrvSqlMq\Parameters\MQSeries"
```

---

## 📞 Error 2043 Details

**What it means:** MQRC_OBJECT_NOT_FOUND
**Where it occurs:** MQOPEN (opening queues)
**When:** Immediately after service starts

**What we know:**
- ✅ MQCONN succeeds (connection to QM works)
- ❌ MQOPEN fails (can't open queues)
- ❌ Happens on ALL 8 queues
- ✅ All queues exist in MQ
- ✅ All security disabled
- ✅ SYSTEM in mqm group

**Likely cause:** Service account permissions issue

---

## 🎯 Next Steps

1. **Test console mode** (see IMMEDIATE ACTION above)
2. Based on result:
   - **Works** → Change service user to MUSR_MQADMIN
   - **Fails** → Read CONVERSATION_SUMMARY.md for detailed analysis

---

## 💾 Full Documentation

For complete details, see:
- `CONVERSATION_SUMMARY.md` - Everything we've done
- `ALTERNATIVE_SOLUTIONS.txt` - Alternative approaches
- `TESTING_GUIDE.md` - Testing procedures

---

**Last Updated:** 2026-02-27 08:15 AM
**Ready to continue!** Start with console mode test above. 🚀
