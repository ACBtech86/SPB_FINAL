# OpenSSL - Guia Rápido de Referência

**Para:** Desenvolvedores do BCSrvSqlMq
**Data:** 27/02/2026

---

## 🚀 Compilação x64

```bash
# 1. Limpar build anterior
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"
rm -rf build

# 2. Configurar CMake para x64
cmake -B build -G "Visual Studio 18 2026" -A x64

# 3. Editar build/BCSrvSqlMq.vcxproj
#    Mudar: <UseOfMfc>Dynamic</UseOfMfc>
#    Para:  <UseOfMfc>false</UseOfMfc>

# 4. Compilar
cmake --build build --config Release

# 5. Executável gerado:
# build/Release/BCSrvSqlMq.exe (237KB, x64)
```

---

## 📝 Configuração do INI

### ⚠️ PENDENTE: Adicionar CertificateFile

O código OpenSSL migrado espera um **arquivo PEM de certificado** em vez do ODBC database.

**Adicionar em BCSrvSqlMq.ini:**
```ini
[Security]
SecurityEnable=S
CertificateFile=C:\BCSrvSqlMq\certificates\public_cert.pem    ; NOVO!
PrivateKeyFile=C:\BCSrvSqlMq\certificates\private_key.pem
PrivateKeyLabel=ChavePrivada
PublicKeyLabel=ChavePublica
KeyPassword=senha_se_houver
SecurityDB=BCSPBSTR   ; Ainda usado se não houver CertificateFile
```

### Exportar Certificado do ODBC para PEM

**Usando OpenSSL CLI:**
```bash
# Se o certificado estiver em formato DER no database
openssl x509 -inform DER -in certificado.der -out public_cert.pem

# Se estiver em formato PEM
cp certificado.pem public_cert.pem
```

**Ou use ferramenta de gerenciamento do database** para exportar o certificado.

---

## 🔧 API do OpenSSL Wrapper

### CryptoContext - Gerenciamento de Chaves

```cpp
#include "OpenSSLWrapper.h"

// Criar contexto
OpenSSLCrypto::CryptoContext ctx;

// Carregar certificado (chave pública)
if (!ctx.LoadPublicKeyFromCertificate("path/to/cert.pem")) {
    const char* error = ctx.GetLastError();
    // tratar erro
}

// Carregar chave privada (com senha opcional)
if (!ctx.LoadPrivateKey("path/to/key.pem", "senha")) {
    const char* error = ctx.GetLastError();
    // tratar erro
}

// Obter informações
int keySize = ctx.GetKeySize();     // Em bits (ex: 1024, 2048)
bool isRSA = ctx.IsRSAKey();        // true se for RSA

// Cleanup automático no destrutor
```

### DigitalSignature - Assinatura/Verificação

```cpp
// Criar assinatura
unsigned char* signature = nullptr;
size_t signatureLen = 0;

bool success = OpenSSLCrypto::DigitalSignature::CreateSignature(
    data,                    // Dados a assinar
    dataLength,              // Tamanho dos dados
    privateKey,              // EVP_PKEY* da chave privada
    &signature,              // [OUT] Assinatura (alocada pelo OpenSSL)
    &signatureLen,           // [OUT] Tamanho da assinatura
    EVP_sha256()            // Algoritmo hash (default: SHA-256)
);

if (success) {
    // Usar signature...
    delete[] signature;  // Liberar memória
}

// Verificar assinatura
bool valid = OpenSSLCrypto::DigitalSignature::VerifySignature(
    data,                    // Dados originais
    dataLength,              // Tamanho
    signature,               // Assinatura a verificar
    signatureLen,            // Tamanho da assinatura
    publicKey,               // EVP_PKEY* da chave pública
    EVP_sha256()            // Algoritmo hash (mesmo usado na assinatura)
);

if (valid) {
    // Assinatura válida!
}
```

---

## 🔑 Funções Criptográficas Migradas

### Assinatura Digital (RSA)

| Função | Algoritmo | Uso |
|--------|-----------|-----|
| `funcAssinar()` | RSA-1024 + MD5/SHA-1 | Assinar mensagens SPB |
| `funcVerifyAss()` | RSA-1024 + MD5/SHA-1 | Verificar assinaturas |

**Parâmetros:**
- `lpSecHeader->AlgHash`: `0x01` = MD5, `0x02` = SHA-1
- `lpSecHeader->NumSerieCertLocal`: Serial number do certificado
- `lpSecHeader->IniHashCifrSign`: Assinatura (128 bytes)

### Criptografia Simétrica (3DES + RSA Key Wrapping)

| Função | Algoritmo | Uso |
|--------|-----------|-----|
| `funcCript()` | 3DES-CBC + RSA-1024 wrap | Criptografar dados |
| `funcDeCript()` | 3DES-CBC + RSA-1024 unwrap | Descriptografar dados |

**Processo:**
1. Gera chave 3DES aleatória (192 bits)
2. Criptografa dados com 3DES-CBC
3. "Envolve" chave 3DES com RSA (key wrapping)
4. Armazena chave criptografada no header

**Parâmetros:**
- `lpSecHeader->AlgSymKey`: `0x01` = 3DES
- `lpSecHeader->NumSerieCertDest`: Serial number do certificado destino
- `lpSecHeader->IniSymKeyCifr`: Chave 3DES criptografada (128 bytes)

---

## ⚠️ Compatibilidade e Limitações

### ✅ Compatível:
- Formato binário de assinaturas (com ajuste de 3 bytes de header)
- Criptografia 3DES-CBC
- RSA 1024-bit
- Serial numbers de certificados
- Algoritmos MD5, SHA-1

### ⚠️ Mudanças:
- **Certificado público:** Arquivo PEM em vez de ODBC database
- **IV do 3DES:** Gerado aleatoriamente (antes: possivelmente fixo)
- **Tratamento de erros:** Mais detalhado

### ❌ Não Suportado:
- ODBC keyset (substituído por arquivos PEM)
- Algoritmos proprietários da CryptLib
- Formatos binários específicos do CryptLib (exceto assinaturas)

---

## 🐛 Troubleshooting

### Erro: "Certificate path is null"
```cpp
// ReadPublicKey() espera CertificateFile no INI
// SOLUÇÃO: Adicionar parâmetro ao InitSrv.cpp para ler do INI
```

### Erro: "Failed to load certificate"
```bash
# Verificar formato do arquivo
openssl x509 -in cert.pem -text -noout

# Converter se necessário
openssl x509 -inform DER -in cert.der -outform PEM -out cert.pem
```

### Erro: "Key size != 1024"
```cpp
// O código atual exige RSA 1024-bit
// Para mudar: editar ReadPublicKey() e ReadPrivatKey()
if (cryptKeySize != 1024)  // Mudar para 2048 se necessário
```

### Erro: "Signature verification failed"
```cpp
// Verificar:
// 1. Algoritmo hash correto (MD5/SHA-1)
// 2. Serial number do certificado
// 3. Formato da assinatura (128 bytes + 3 bytes header?)
```

---

## 📚 Recursos Externos

### OpenSSL Oficial
- **Documentação:** https://www.openssl.org/docs/man3.0/
- **EVP API:** https://www.openssl.org/docs/man3.0/man7/evp.html
- **X.509:** https://www.openssl.org/docs/man3.0/man3/X509_get_pubkey.html

### Exemplos OpenSSL
```bash
# Gerar chave privada RSA
openssl genrsa -out private.pem 2048

# Extrair chave pública
openssl rsa -in private.pem -pubout -out public.pem

# Gerar certificado autoassinado
openssl req -new -x509 -key private.pem -out cert.pem -days 365

# Ver informações do certificado
openssl x509 -in cert.pem -text -noout
```

---

## 🔄 Atualizações Futuras Recomendadas

### Alta Prioridade:
1. **RSA 2048-bit** - Mais seguro que 1024-bit
2. **SHA-256** - Mais seguro que SHA-1/MD5
3. **Validação de certificados** - Verificar validade, revogação

### Média Prioridade:
4. **AES-256** - Substituir 3DES (mais rápido e seguro)
5. **GCM mode** - Autenticação integrada (em vez de CBC)
6. **OAEP padding** - Para RSA key wrapping

### Baixa Prioridade:
7. **Curvas elípticas (ECC)** - Alternativa moderna ao RSA
8. **Hardware security modules (HSM)** - Para produção crítica

---

**Última atualização:** 27/02/2026
**Versão:** 1.0
