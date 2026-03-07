# 🔐 Cryptographic Testing Guide

## Overview

This guide explains how to test the OpenSSL 3.6.1 integration with the real certificates.

The test will verify:
- ✅ Certificate loading (public_cert.pem)
- ✅ Private key loading (private.key)
- ✅ Digital signatures (funcAssinar)
- ✅ Signature verification (funcVerifyAss)
- ✅ Encryption (funcCript)
- ✅ Decryption (funcDeCript)

---

## Quick Start

### Method 1: Using Visual Studio Command Prompt (Recommended)

1. **Open "x64 Native Tools Command Prompt for VS 2022"**
   - Start Menu → Visual Studio 2022 → x64 Native Tools Command Prompt

2. **Navigate to project**
   ```cmd
   cd "C:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"
   ```

3. **Run the compilation script**
   ```cmd
   compile_crypto_test.bat
   ```

4. **View results**
   - The test will compile and run automatically
   - Look for "ALL TESTS PASSED" message

---

### Method 2: Manual Compilation

If you prefer to compile manually:

```cmd
cd "C:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"

cl /std:c++17 /EHsc /O2 test_crypto_full.cpp ^
   /I"C:\vcpkg\installed\x64-windows\include" ^
   /link ^
   /LIBPATH:"C:\vcpkg\installed\x64-windows\lib" ^
   libcrypto.lib libssl.lib ^
   /OUT:build\Release\test_crypto_full.exe

build\Release\test_crypto_full.exe
```

---

## Test Details

### Test File: `test_crypto_full.cpp`

This comprehensive test program:

**1. Loads Public Certificate**
```
Path: certificates/public_cert.pem
Extracts: X.509 certificate, public key
Verifies: Subject, issuer, key size
```

**2. Loads Private Key**
```
Path: certificates/private.key
Extracts: RSA private key
Verifies: Key type, key size
```

**3. Creates Digital Signature**
```
Algorithm: RSA with SHA-256
Input: Test message
Output: Digital signature (256 bytes for 2048-bit RSA)
```

**4. Verifies Signature**
```
Uses: Public key from certificate
Verifies: Signature matches message
Result: PASS/FAIL
```

**5. Encrypts Message**
```
Algorithm: RSA with OAEP padding
Input: Test message
Output: Encrypted ciphertext
```

**6. Decrypts Message**
```
Algorithm: RSA with OAEP padding
Input: Ciphertext from step 5
Output: Original message (verified)
```

---

## Expected Output

### Success Case

```
========================================
BCSrvSqlMq - Full Cryptographic Test
OpenSSL 3.6.1 - x64 Architecture
========================================
OpenSSL Version: OpenSSL 3.6.1 27 Jan 2026

[TEST 1] Loading Public Certificate
   Path: C:\Users\...\certificates\public_cert.pem
   Subject: /CN=FINVEST...
   Key Size: 2048 bits
   ✅ SUCCESS: Public certificate loaded

[TEST 2] Loading Private Key
   Path: C:\Users\...\certificates\private.key
   Key Size: 2048 bits
   Key Type: RSA
   ✅ SUCCESS: Private key loaded

[TEST 3] Digital Signature (funcAssinar)
   Message: "Hello from BCSrvSqlMq x64 with OpenSSL 3.6.1!"
   Signature (256 bytes): 8A3F2E1D...
   ✅ SUCCESS: Digital signature created (256 bytes)

[TEST 4] Signature Verification (funcVerifyAss)
   ✅ SUCCESS: Signature verification PASSED

[TEST 5] Encryption (funcCript)
   Message: "Hello from BCSrvSqlMq x64 with OpenSSL 3.6.1!"
   Ciphertext (256 bytes): F4E9A7B3...
   ✅ SUCCESS: Message encrypted (256 bytes)

[TEST 6] Decryption (funcDeCript)
   Decrypted: "Hello from BCSrvSqlMq x64 with OpenSSL 3.6.1!"
   ✅ SUCCESS: Decryption correct - matches original message!

========================================
TEST SUMMARY
========================================
Tests Passed: 6 / 6

🎉 ALL TESTS PASSED! 🎉

✅ The x64 OpenSSL 3.6.1 migration is FULLY FUNCTIONAL!
✅ Certificate loading works correctly
✅ Digital signatures work correctly
✅ Signature verification works correctly
✅ Encryption works correctly
✅ Decryption works correctly

The service is ready for production use!
```

---

## Troubleshooting

### Error: "Cannot open certificate file"
**Solution:** Verify certificates exist:
```cmd
dir certificates\*.pem
dir certificates\*.key
```

### Error: "Cannot parse certificate"
**Solution:** Verify certificate format:
```cmd
openssl x509 -in certificates\public_cert.pem -text -noout
```

### Error: "libcrypto-3-x64.dll not found"
**Solution:** Copy OpenSSL DLLs:
```cmd
copy "C:\vcpkg\installed\x64-windows\bin\libcrypto-3-x64.dll" build\Release\
copy "C:\vcpkg\installed\x64-windows\bin\libssl-3-x64.dll" build\Release\
```

### Error: "'cl' is not recognized"
**Solution:** Use "x64 Native Tools Command Prompt for VS 2022", not regular Command Prompt

---

## What This Proves

✅ **OpenSSL 3.6.1 is correctly integrated**
- Headers found and linked
- Libraries loaded at runtime
- API calls working correctly

✅ **Certificates are correctly formatted**
- PEM format valid
- Public certificate parseable
- Private key parseable

✅ **All crypto functions work**
- RSA key operations
- SHA-256 hashing
- Digital signatures (sign + verify)
- Encryption/decryption with OAEP padding

✅ **Service is ready for production**
- When messages arrive via MQ
- ThreadMQ will call funcAssinar/funcCript
- These functions will work correctly
- No code changes needed

---

## Files

| File | Purpose |
|------|---------|
| `test_crypto_full.cpp` | Complete cryptographic test source |
| `compile_crypto_test.bat` | Compilation script |
| `CRYPTO_TEST_README.md` | This file |
| `certificates/public_cert.pem` | Public certificate (test input) |
| `certificates/private.key` | Private key (test input) |
| `build/Release/test_crypto_full.exe` | Compiled test (output) |

---

## Next Steps After Testing

Once all tests pass:

1. **Service is production-ready** for crypto operations
2. **Configure MQ queues** to allow message flow
3. **Monitor first encrypted message** in service logs
4. **Verify end-to-end** encryption in production

---

**Date:** 2026-03-01
**Migration:** 32-bit CryptLib → 64-bit OpenSSL 3.6.1
**Status:** Ready for testing
