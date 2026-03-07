# Archived Backup Files

**Archive Date**: 01/03/2026 17:52:30,54

## Files Archived

- **cmqc.h.STUB_BACKUP** - Stub MQ header that caused structure mismatch

## What Was Wrong

The stub header had:
- Simplified MQOD structure definition
- Different structure layout than real IBM MQ 9.4.5.0
- MQOD_DEFAULT with ObjectType = 0 (should be 1)

This caused error 2043/2085 because ObjectType was written to wrong memory offset.

## Resolution

- Removed stub header
- Rebuilt with real IBM MQ headers from C:\Program Files\IBM\MQ\tools\c\include\
- All 8 tasks now working correctly

## Do Not Use This File!

This stub header is incompatible with IBM MQ 9.4.5.0 runtime.
It is kept only for reference to understand the issue.

