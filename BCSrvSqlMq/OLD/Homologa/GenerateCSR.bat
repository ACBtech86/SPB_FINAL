set OPENSSL_CONF=C:\Program Files\OpenSSL-Win64\bin\cnf\openssl.cfg

"C:\Program Files\OpenSSL-Win64\bin\openssl.exe" req -sha256 -newkey rsa:2048 -keyout SPBT006.key  -out SPBT006.csr -subj "/CN=FINVEST DISTRIBUIDORA DE TITULOS E VALORES MOBILIARIOS LTDA T006/OU=ISPB-36266751/OU=SISBACEN-43011/O=ICP-Brasil/L=SAO PAULO/ST=SP/C=BR"

echo CSR and Private Key generated successfully!
echo Verifying CSR details:

"C:\Program Files\OpenSSL-Win64\bin\openssl.exe" req -text  -verify -in SPBT006.csr

pause