# convert_pfx_to_pem.ps1
# Convert .pfx file to separate .pem (certificate) and .key (private key) files
# Can use either OpenSSL (if available) or built-in .NET classes
#
# Usage:
#   .\convert_pfx_to_pem.ps1 -PfxFile "certificate.pfx" -Password "mypassword"
#   .\convert_pfx_to_pem.ps1 -PfxFile "certificate.pfx"  # Will prompt for password
#
# Output:
#   - public_cert.pem  (certificate)
#   - private.key      (private key)

param(
    [Parameter(Mandatory=$false)]
    [string]$PfxFile = "",

    [Parameter(Mandatory=$false)]
    [string]$Password = "",

    [Parameter(Mandatory=$false)]
    [string]$CertOutput = "public_cert.pem",

    [Parameter(Mandatory=$false)]
    [string]$KeyOutput = "private.key",

    [Parameter(Mandatory=$false)]
    [switch]$UseOpenSSL = $false
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "PFX to PEM/KEY Converter" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if PFX file was provided
if ([string]::IsNullOrEmpty($PfxFile)) {
    Write-Host "ERROR: Please specify PFX file" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host '  .\convert_pfx_to_pem.ps1 -PfxFile "certificate.pfx" -Password "mypassword"'
    Write-Host '  .\convert_pfx_to_pem.ps1 -PfxFile "certificate.pfx"  # Will prompt for password'
    Write-Host ""
    exit 1
}

# Check if PFX file exists
if (-not (Test-Path $PfxFile)) {
    Write-Host "ERROR: PFX file not found: $PfxFile" -ForegroundColor Red
    exit 1
}

Write-Host "Input:  $PfxFile" -ForegroundColor Green
Write-Host "Output: $CertOutput (certificate)" -ForegroundColor Green
Write-Host "        $KeyOutput (private key)" -ForegroundColor Green
Write-Host ""

# Get password if not provided
if ([string]::IsNullOrEmpty($Password)) {
    $securePassword = Read-Host "Enter PFX password (or press Enter if no password)" -AsSecureString
} else {
    $securePassword = ConvertTo-SecureString -String $Password -Force -AsPlainText
}

# Check if OpenSSL is available
$opensslPath = $null
$possiblePaths = @(
    "C:\Program Files\OpenSSL-Win64\bin\openssl.exe",
    "C:\OpenSSL-Win64\bin\openssl.exe",
    "openssl.exe"
)

foreach ($path in $possiblePaths) {
    try {
        if (Get-Command $path -ErrorAction SilentlyContinue) {
            $opensslPath = $path
            break
        }
    } catch { }
}

# Decide which method to use
$useBuiltIn = $true
if ($opensslPath -and $UseOpenSSL) {
    Write-Host "Using OpenSSL: $opensslPath" -ForegroundColor Yellow
    $useBuiltIn = $false
} elseif ($opensslPath) {
    Write-Host "OpenSSL available but using built-in .NET method" -ForegroundColor Yellow
    Write-Host "Use -UseOpenSSL switch to use OpenSSL instead" -ForegroundColor Gray
} else {
    Write-Host "Using built-in .NET classes (OpenSSL not found)" -ForegroundColor Yellow
}
Write-Host ""

# ============================================
# Method 1: Built-in .NET (No OpenSSL needed)
# ============================================
if ($useBuiltIn) {
    try {
        # Step 1: Load PFX
        Write-Host "Step 1: Loading PFX file..." -ForegroundColor Cyan

        $pfxBytes = [System.IO.File]::ReadAllBytes($PfxFile)
        $pfx = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2

        try {
            $pfx.Import($pfxBytes, $securePassword, [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable)
            Write-Host "  SUCCESS - PFX loaded" -ForegroundColor Green
        } catch {
            Write-Host "  ERROR: Failed to load PFX - wrong password?" -ForegroundColor Red
            Write-Host "  Details: $($_.Exception.Message)" -ForegroundColor Gray
            exit 1
        }

        # Step 2: Display certificate info
        Write-Host ""
        Write-Host "Step 2: Certificate Information:" -ForegroundColor Cyan
        Write-Host "  Subject:     $($pfx.Subject)" -ForegroundColor White
        Write-Host "  Issuer:      $($pfx.Issuer)" -ForegroundColor White
        Write-Host "  Thumbprint:  $($pfx.Thumbprint)" -ForegroundColor White
        Write-Host "  Valid From:  $($pfx.NotBefore)" -ForegroundColor White
        Write-Host "  Valid Until: $($pfx.NotAfter)" -ForegroundColor White
        Write-Host "  Has Private: $($pfx.HasPrivateKey)" -ForegroundColor White

        if (-not $pfx.HasPrivateKey) {
            Write-Host ""
            Write-Host "WARNING: PFX does not contain a private key!" -ForegroundColor Yellow
            Write-Host "Only the certificate will be exported." -ForegroundColor Yellow
        }

        # Step 3: Export certificate
        Write-Host ""
        Write-Host "Step 3: Exporting certificate..." -ForegroundColor Cyan

        $certBytes = $pfx.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
        $certBase64 = [System.Convert]::ToBase64String($certBytes)

        $certPem = "-----BEGIN CERTIFICATE-----`n"
        for ($i = 0; $i -lt $certBase64.Length; $i += 64) {
            $length = [Math]::Min(64, $certBase64.Length - $i)
            $certPem += $certBase64.Substring($i, $length) + "`n"
        }
        $certPem += "-----END CERTIFICATE-----`n"

        [System.IO.File]::WriteAllText($CertOutput, $certPem)
        Write-Host "  SUCCESS - Certificate saved to $CertOutput" -ForegroundColor Green

        # Step 4: Export private key
        if ($pfx.HasPrivateKey) {
            Write-Host ""
            Write-Host "Step 4: Exporting private key..." -ForegroundColor Cyan

            # Ask about encryption
            Write-Host ""
            Write-Host "Private key export options:" -ForegroundColor Yellow
            Write-Host "  1. Unencrypted (no password - easier to use)" -ForegroundColor White
            Write-Host "  2. Encrypted (with password - more secure)" -ForegroundColor White
            Write-Host ""

            $choice = Read-Host "Enter choice [1/2]"

            if ($choice -eq "2") {
                Write-Host ""
                Write-Host "NOTE: .NET cannot export encrypted private keys directly" -ForegroundColor Yellow
                Write-Host "The key will be exported unencrypted, then encrypted with OpenSSL" -ForegroundColor Yellow

                if (-not $opensslPath) {
                    Write-Host ""
                    Write-Host "ERROR: OpenSSL required for encrypted private key export" -ForegroundColor Red
                    Write-Host "Please install OpenSSL or choose option 1 (unencrypted)" -ForegroundColor Yellow
                    exit 1
                }

                $encrypt = $true
            } else {
                $encrypt = $false
            }

            # Export private key (RSA format)
            try {
                $privateKey = $pfx.PrivateKey

                # Export as PKCS#8 PEM format
                $keyBytes = $privateKey.ExportPkcs8PrivateKey()
                $keyBase64 = [System.Convert]::ToBase64String($keyBytes)

                $keyPem = "-----BEGIN PRIVATE KEY-----`n"
                for ($i = 0; $i -lt $keyBase64.Length; $i += 64) {
                    $length = [Math]::Min(64, $keyBase64.Length - $i)
                    $keyPem += $keyBase64.Substring($i, $length) + "`n"
                }
                $keyPem += "-----END PRIVATE KEY-----`n"

                [System.IO.File]::WriteAllText($KeyOutput, $keyPem)
                Write-Host "  SUCCESS - Private key saved to $KeyOutput" -ForegroundColor Green

                # Encrypt if requested
                if ($encrypt) {
                    Write-Host ""
                    Write-Host "Step 5: Encrypting private key..." -ForegroundColor Cyan

                    $keyPassword = Read-Host "Enter password for private key" -AsSecureString
                    $keyPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($keyPassword))

                    $tempKey = "$KeyOutput.tmp"
                    Move-Item $KeyOutput $tempKey -Force

                    & $opensslPath rsa -aes256 -in $tempKey -out $KeyOutput -passout "pass:$keyPasswordPlain"

                    Remove-Item $tempKey -Force
                    Write-Host "  SUCCESS - Private key encrypted" -ForegroundColor Green
                }

            } catch {
                Write-Host "  ERROR: Failed to export private key" -ForegroundColor Red
                Write-Host "  Details: $($_.Exception.Message)" -ForegroundColor Gray
                exit 1
            }
        }

    } catch {
        Write-Host "ERROR: Conversion failed" -ForegroundColor Red
        Write-Host "Details: $($_.Exception.Message)" -ForegroundColor Gray
        exit 1
    }
}

# ============================================
# Method 2: OpenSSL
# ============================================
else {
    # Convert secure string to plain text for OpenSSL
    $passwordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword))

    # Step 1: Extract certificate
    Write-Host "Step 1: Extracting certificate with OpenSSL..." -ForegroundColor Cyan

    if ([string]::IsNullOrEmpty($passwordPlain)) {
        & $opensslPath pkcs12 -in $PfxFile -clcerts -nokeys -out $CertOutput
    } else {
        & $opensslPath pkcs12 -in $PfxFile -clcerts -nokeys -out $CertOutput -password "pass:$passwordPlain"
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to extract certificate" -ForegroundColor Red
        exit 1
    }
    Write-Host "  SUCCESS - Certificate saved to $CertOutput" -ForegroundColor Green

    # Step 2: Extract private key
    Write-Host ""
    Write-Host "Step 2: Extracting private key..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Private key export options:" -ForegroundColor Yellow
    Write-Host "  1. Unencrypted (no password - easier to use)" -ForegroundColor White
    Write-Host "  2. Encrypted (with password - more secure)" -ForegroundColor White
    Write-Host ""

    $choice = Read-Host "Enter choice [1/2]"

    if ($choice -eq "2") {
        # Encrypted
        if ([string]::IsNullOrEmpty($passwordPlain)) {
            & $opensslPath pkcs12 -in $PfxFile -nocerts -out $KeyOutput
        } else {
            & $opensslPath pkcs12 -in $PfxFile -nocerts -out $KeyOutput -password "pass:$passwordPlain"
        }
    } else {
        # Unencrypted
        if ([string]::IsNullOrEmpty($passwordPlain)) {
            & $opensslPath pkcs12 -in $PfxFile -nocerts -nodes -out $KeyOutput
        } else {
            & $opensslPath pkcs12 -in $PfxFile -nocerts -nodes -out $KeyOutput -password "pass:$passwordPlain"
        }
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to extract private key" -ForegroundColor Red
        exit 1
    }
    Write-Host "  SUCCESS - Private key saved to $KeyOutput" -ForegroundColor Green
}

# Final verification
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Conversion Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Files created:" -ForegroundColor White
Write-Host "  - $CertOutput  (certificate for verification/encryption)" -ForegroundColor Green
Write-Host "  - $KeyOutput    (private key for signing/decryption)" -ForegroundColor Green
Write-Host ""
Write-Host "Update BCSrvSqlMq.ini:" -ForegroundColor Yellow
Write-Host "[Security]" -ForegroundColor Gray
Write-Host "CertificateFile=$(Resolve-Path $CertOutput)" -ForegroundColor Gray
Write-Host "PrivateKeyFile=$(Resolve-Path $KeyOutput)" -ForegroundColor Gray
Write-Host ""

# Verify certificate
Write-Host "Certificate verification:" -ForegroundColor Yellow
if ($opensslPath) {
    & $opensslPath x509 -in $CertOutput -subject -issuer -dates -noout
} else {
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($CertOutput)
    Write-Host "Subject: $($cert.Subject)"
    Write-Host "Issuer:  $($cert.Issuer)"
    Write-Host "Valid:   $($cert.NotBefore) to $($cert.NotAfter)"
}
Write-Host ""
