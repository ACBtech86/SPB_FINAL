# 🎯 PFX to PEM/KEY Conversion Guide

**Perfect!** `.pfx` files contain **both certificate AND private key** in one file!

This is the **complete solution** - you get everything you need from a single file.

---

## ⚡ Quick Start

### Option 1: PowerShell (Recommended - Works Without OpenSSL!)

```powershell
cd tools
.\convert_pfx_to_pem.ps1 -PfxFile "certificate.pfx" -Password "mypassword"
```

Or let it prompt for password:
```powershell
.\convert_pfx_to_pem.ps1 -PfxFile "certificate.pfx"
```

### Option 2: Batch Script (Requires OpenSSL)

```cmd
cd tools
convert_pfx_to_pem.bat certificate.pfx mypassword
```

### Option 3: Direct OpenSSL Commands

```bash
# Extract certificate (public key)
openssl pkcs12 -in certificate.pfx -clcerts -nokeys -out public_cert.pem

# Extract private key (unencrypted)
openssl pkcs12 -in certificate.pfx -nocerts -nodes -out private.key

# Extract private key (encrypted with password)
openssl pkcs12 -in certificate.pfx -nocerts -out private.key
```

---

## 📋 What You Get

From a single `.pfx` file, you'll extract:

| File | Contains | Used For | Required For |
|------|----------|----------|--------------|
| **public_cert.pem** | Certificate + Public Key | Signature verification, Encryption | ReadPublicKey(), funcVerifyAss(), funcCript() |
| **private.key** | RSA Private Key | Signature creation, Decryption | ReadPrivatKey(), funcAssinar(), funcDeCript() |

---

## 🔧 Step-by-Step Example

### Scenario: You have `server_certificate.pfx` with password "SecurePass123"

**1. Run the converter:**

```powershell
cd C:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\tools

.\convert_pfx_to_pem.ps1 -PfxFile "C:\Certificates\server_certificate.pfx" -Password "SecurePass123"
```

**2. Expected Output:**

```
==========================================
PFX to PEM/KEY Converter
==========================================

Input:  C:\Certificates\server_certificate.pfx
Output: public_cert.pem (certificate)
        private.key (private key)

Using built-in .NET classes (OpenSSL not found)

Step 1: Loading PFX file...
  SUCCESS - PFX loaded

Step 2: Certificate Information:
  Subject:     CN=yourserver.spb.net.br
  Issuer:      CN=CA Authority
  Thumbprint:  A1B2C3D4E5F6789...
  Valid From:  01/01/2024 00:00:00
  Valid Until: 31/12/2025 23:59:59
  Has Private: True

Step 3: Exporting certificate...
  SUCCESS - Certificate saved to public_cert.pem

Step 4: Exporting private key...

Private key export options:
  1. Unencrypted (no password - easier to use)
  2. Encrypted (with password - more secure)

Enter choice [1/2]: 1
  SUCCESS - Private key saved to private.key

==========================================
Conversion Complete!
==========================================

Files created:
  - public_cert.pem  (certificate for verification/encryption)
  - private.key      (private key for signing/decryption)

Update BCSrvSqlMq.ini:
[Security]
CertificateFile=C:\BCSrvSqlMq\certificates\public_cert.pem
PrivateKeyFile=C:\BCSrvSqlMq\certificates\private.key
```

**3. Move files to certificates folder:**

```powershell
Move-Item public_cert.pem ..\certificates\
Move-Item private.key ..\certificates\
```

**4. Update BCSrvSqlMq.ini:**

```ini
[Security]
SecurityEnable=S
CertificateFile=C:\BCSrvSqlMq\certificates\public_cert.pem
PrivateKeyFile=C:\BCSrvSqlMq\certificates\private.key
PublicKeyLabel=yourserver.spb.net.br
PrivateKeyLabel=SPB Key
KeyPassword=
```

**Done!** ✅

---

## 🔐 Private Key Encryption Options

You'll be asked to choose:

### Option 1: Unencrypted Private Key (Recommended for Testing)

**Pros:**
- ✅ Easier to use - no password needed
- ✅ Service starts automatically without password prompt
- ✅ Simpler configuration

**Cons:**
- ❌ Less secure - anyone with file access can use the key
- ❌ Should set strict file permissions

**Configuration:**
```ini
[Security]
PrivateKeyFile=C:\BCSrvSqlMq\certificates\private.key
KeyPassword=
```

**Secure the file:**
```cmd
icacls C:\BCSrvSqlMq\certificates\private.key /inheritance:r
icacls C:\BCSrvSqlMq\certificates\private.key /grant:r "NT AUTHORITY\NETWORK SERVICE:R"
icacls C:\BCSrvSqlMq\certificates\private.key /grant:r "Administrators:F"
```

### Option 2: Encrypted Private Key (Recommended for Production)

**Pros:**
- ✅ More secure - requires password to use
- ✅ Better protection if file is copied/stolen

**Cons:**
- ❌ Password must be stored in BCSrvSqlMq.ini
- ❌ Slightly slower to load

**Configuration:**
```ini
[Security]
PrivateKeyFile=C:\BCSrvSqlMq\certificates\private.key
KeyPassword=YourEncryptionPassword
```

**NOTE:** The password in the INI file must match the password used to encrypt the private key!

---

## 🔍 Verification

After conversion, always verify:

### 1. Check certificate file:
```bash
openssl x509 -in public_cert.pem -text -noout
```

Expected:
```
Certificate:
    Data:
        Version: 3 (0x2)
        Subject: CN=yourserver.spb.net.br
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (1024 bit)
```

### 2. Check private key file:
```bash
openssl rsa -in private.key -check -noout
```

Expected:
```
RSA key ok
```

### 3. Verify certificate and key match:
```bash
# Get certificate modulus
openssl x509 -noout -modulus -in public_cert.pem | openssl md5

# Get private key modulus
openssl rsa -noout -modulus -in private.key | openssl md5
```

**Both MD5 hashes MUST match!**

### 4. Test loading in OpenSSL:
```bash
# Test certificate
openssl x509 -in public_cert.pem -noout

# Test private key (unencrypted)
openssl rsa -in private.key -check -noout

# Test private key (encrypted)
openssl rsa -in private.key -check -noout -passin pass:YourPassword
```

---

## 📁 File Structure After Conversion

```
C:\BCSrvSqlMq\
├── certificates\
│   ├── public_cert.pem       ← Certificate (X.509 in PEM format)
│   ├── private.key           ← Private Key (RSA in PEM format)
│   └── server_certificate.pfx ← Original PFX (keep as backup!)
├── tools\
│   ├── convert_pfx_to_pem.ps1 ← PowerShell converter
│   └── convert_pfx_to_pem.bat ← Batch converter
└── BCSrvSqlMq.ini
```

---

## 🆘 Troubleshooting

### Error: "Wrong password" or "Failed to load PFX"

**Causes:**
- Incorrect password
- Corrupted PFX file
- PFX is actually a different format

**Solutions:**
1. Try opening PFX in Windows (double-click) to verify password
2. Check password for typos
3. Try empty password (some PFX files have no password):
   ```powershell
   .\convert_pfx_to_pem.ps1 -PfxFile "certificate.pfx" -Password ""
   ```

### Error: "PFX does not contain a private key"

**Cause:** The PFX only contains the certificate, not the private key

**Solutions:**
1. You need a different PFX that contains the private key
2. Contact the certificate issuer for the complete PFX
3. Use the certificate from PFX + a separate .key file

### Error: "OpenSSL not found"

**Solution 1:** Use PowerShell method (doesn't need OpenSSL)
```powershell
.\convert_pfx_to_pem.ps1 -PfxFile "certificate.pfx"
```

**Solution 2:** Install OpenSSL
```cmd
winget install ShiningLight.OpenSSL
```

### Error: "Cannot export encrypted private key"

**Cause:** .NET cannot export encrypted keys directly

**Solutions:**
1. Export as unencrypted, then encrypt separately:
   ```bash
   # Export unencrypted first
   .\convert_pfx_to_pem.ps1 -PfxFile "certificate.pfx"

   # Then encrypt with OpenSSL
   openssl rsa -aes256 -in private.key -out private_encrypted.key
   ```

2. Use OpenSSL method directly:
   ```bash
   openssl pkcs12 -in certificate.pfx -nocerts -out private.key
   # OpenSSL will prompt for PFX password and new key password
   ```

### Warning: "Certificate and key DO NOT match"

**Cause:** The certificate and private key are from different key pairs

**Impact:**
- ❌ Signatures won't verify
- ❌ Encryption/decryption will fail

**Solutions:**
1. Verify you used the correct PFX file
2. Re-export from the PFX
3. Check if PFX contains multiple certificates (use the right one)

---

## 🔒 Security Best Practices

### 1. File Permissions

**For unencrypted private key:**
```cmd
# Remove inheritance
icacls private.key /inheritance:r

# Grant read to service account only
icacls private.key /grant:r "NT AUTHORITY\NETWORK SERVICE:R"

# Grant full control to admins
icacls private.key /grant:r "Administrators:F"
```

**For encrypted private key:**
```cmd
# Still restrict, but less critical since file is encrypted
icacls private.key /inheritance:r
icacls private.key /grant:r "NT AUTHORITY\NETWORK SERVICE:R"
icacls private.key /grant:r "Administrators:F"
```

### 2. Password Storage

**If using encrypted private key:**

❌ **BAD:**
```ini
[Security]
KeyPassword=password123
```

✅ **BETTER:**
```ini
[Security]
KeyPassword=%ENV_PRIVATE_KEY_PASSWORD%
```

Then set environment variable:
```cmd
setx PRIVATE_KEY_PASSWORD "YourStrongPassword" /M
```

✅ **BEST:**
Use Windows Data Protection API (DPAPI) - requires code changes

### 3. Backup

**Keep the original PFX secure:**
- Store in secure location with access control
- Include password in secure password manager
- Document where it's stored
- Have a disaster recovery plan

---

## 📊 Format Comparison

| Format | Contains | Encrypted | Use Case |
|--------|----------|-----------|----------|
| **.pfx / .p12** | Cert + Private Key | Usually | **Transport/backup** (one file with everything) |
| **.pem (cert)** | Certificate only | No | **OpenSSL apps** (BCSrvSqlMq certificate) |
| **.pem (key)** | Private key only | Optional | **OpenSSL apps** (BCSrvSqlMq private key) |
| **.cer** | Certificate only | No | Windows apps, email |
| **.key** | Private key only | Optional | Web servers, SSH |
| **.crt** | Certificate only | No | Linux/Apache servers |

---

## ✅ Quick Checklist

After PFX conversion:

- [ ] **Files created**
  - [ ] public_cert.pem exists
  - [ ] private.key exists

- [ ] **Verification**
  - [ ] Certificate loads successfully
  - [ ] Private key loads successfully
  - [ ] Certificate and key modulus match

- [ ] **Configuration**
  - [ ] BCSrvSqlMq.ini updated with file paths
  - [ ] SecurityEnable=S
  - [ ] KeyPassword set (if using encrypted key)

- [ ] **Security**
  - [ ] File permissions restricted
  - [ ] Original PFX backed up securely
  - [ ] Password documented (if encrypted)

- [ ] **Testing**
  - [ ] Service starts without errors
  - [ ] Certificates load in ReadPublicKey/ReadPrivatKey
  - [ ] Crypto functions work (sign/verify/encrypt/decrypt)

---

## 🎓 Advanced: Extract Additional Items

### Extract ALL Certificates from PFX (including CA chain):

```bash
openssl pkcs12 -in certificate.pfx -out complete_chain.pem -nodes
```

This creates a file with:
- Your certificate
- Intermediate CA certificates
- Root CA certificate

### Extract Only CA Certificates:

```bash
openssl pkcs12 -in certificate.pfx -cacerts -nokeys -out ca_chain.pem
```

### View PFX Contents Without Extracting:

```bash
openssl pkcs12 -in certificate.pfx -info -noout
```

---

**Created:** 2026-03-01
**For:** BCSrvSqlMq OpenSSL Migration
**Complete Guide:** PFX → PEM + KEY conversion
