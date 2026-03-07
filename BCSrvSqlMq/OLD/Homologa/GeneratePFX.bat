@echo off
set OPENSSL_BIN=C:\OpenSSL-Win64\bin
set KEY_FILE=SPBT006.key
set CER_FILE=SPBT006.cer
set PFX_FILE= SPBT006.pfx

echo  %OPENSSL_BIN%\openssl.exe pkcs12 -export -out %PFX_FILE% -inkey %KEY_FILE% -in %CER_FILE% 
pause
%OPENSSL_BIN%\openssl.exe pkcs12 -export -out %PFX_FILE% -inkey %KEY_FILE% -in %CER_FILE% 
echo PFX generated successfully!
pause