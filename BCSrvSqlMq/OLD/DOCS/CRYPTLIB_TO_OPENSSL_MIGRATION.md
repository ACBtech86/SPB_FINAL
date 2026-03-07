# Migração CryptLib → OpenSSL 3.6.1

## 📋 Resumo da Análise

### Arquivos Afetados:
- **InitSrv.cpp** (linhas 221-241)
- **ThreadMQ.cpp** (linhas 78-729)

### Funcionalidade Atual:
O código usa **CryptLib 3.2 (CL32.dll)** para:
1. ✅ **Assinatura digital RSA** (1024-bit)
2. ✅ **Verificação de assinaturas**
3. ✅ **Gerenciamento de certificados** (ODBC keyset)
4. ✅ **Chaves públicas/privadas**

---

## 🔄 Mapeamento de Funções

### InitSrv.cpp

| CryptLib | OpenSSL | Descrição |
|----------|---------|-----------|
| `cryptInit()` | `OpenSSL_add_all_algorithms()` | Inicializar biblioteca |
| `cryptEnd()` | `EVP_cleanup()` | Limpar recursos |
| `cryptStatusError()` | `ERR_get_error()` | Checar erros |

### ThreadMQ.cpp - Gerenciamento de Chaves

| CryptLib | OpenSSL | Descrição |
|----------|---------|-----------|
| `cryptKeysetOpen()` | `BIO_new_file()` + `PEM_read_bio_X509()` | Abrir certificado |
| `cryptKeysetClose()` | `BIO_free()` | Fechar arquivo |
| `cryptGetPublicKey()` | `X509_get_pubkey()` | Obter chave pública |
| `cryptGetPrivateKey()` | `PEM_read_bio_PrivateKey()` | Obter chave privada |
| `cryptDestroyContext()` | `EVP_PKEY_free()` | Liberar chave |

### ThreadMQ.cpp - Assinatura Digital

| CryptLib | OpenSSL | Descrição |
|----------|---------|-----------|
| `cryptCreateSignature()` | `EVP_DigestSign()` | Criar assinatura |
| `cryptCheckSignature()` | `EVP_DigestVerify()` | Verificar assinatura |
| `cryptSetAttribute()` | Propriedades da chave | Configurar contexto |
| `cryptGetAttribute()` | `EVP_PKEY_bits()` | Obter tamanho da chave |

---

## 📝 Plano de Migração

### Fase 1: Preparação (1-2 horas)
1. ✅ **Já feito**: OpenSSL 3.6.1 instalado
   - libcrypto-3.dll (3.3MB)
   - libssl-3.dll (701KB)
2. ⬜ Criar header wrapper `OpenSSLWrapper.h`
3. ⬜ Criar implementação `OpenSSLWrapper.cpp`

### Fase 2: InitSrv.cpp (30 minutos)
**Código Atual:**
```cpp
int cryptStatus = cryptInit();
if(cryptStatusError(cryptStatus)) {
    // Error handling
}
```

**Novo Código OpenSSL:**
```cpp
// No arquivo: InitSrv.cpp linha ~221
#include <openssl/evp.h>
#include <openssl/err.h>

// Inicializar OpenSSL
OpenSSL_add_all_algorithms();
ERR_load_crypto_strings();

// No final (linha ~237), substituir cryptEnd():
EVP_cleanup();
ERR_free_strings();
```

### Fase 3: ThreadMQ.cpp - Carregar Certificados (2-3 horas)

**Código Atual (CryptLib):**
```cpp
// Linha 682
cryptKeysetOpen(&m_cryptKeyset, CRYPT_UNUSED, CRYPT_KEYSET_ODBC,
                pMainSrv->pInitSrv->m_SecurityDB, CRYPT_KEYOPT_READONLY);
cryptGetPublicKey(m_cryptKeyset, &m_cryptPublicContext, CRYPT_KEYID_NAME,
                  pMainSrv->pInitSrv->m_PublicKeyLabel);
```

**Novo Código OpenSSL:**
```cpp
#include <openssl/x509.h>
#include <openssl/pem.h>
#include <openssl/bio.h>

// Carregar certificado (chave pública)
BIO* certBio = BIO_new_file("path/to/certificate.pem", "r");
if (!certBio) {
    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8079, FALSE,
                                   &errno, NULL, NULL, NULL, NULL);
    return false;
}

X509* cert = PEM_read_bio_X509(certBio, NULL, NULL, NULL);
if (!cert) {
    BIO_free(certBio);
    unsigned long err = ERR_get_error();
    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8080, FALSE,
                                   &err, NULL, NULL, NULL, NULL);
    return false;
}

// Extrair chave pública
EVP_PKEY* pubKey = X509_get_pubkey(cert);
if (!pubKey) {
    X509_free(cert);
    BIO_free(certBio);
    return false;
}

// Verificar algoritmo RSA
if (EVP_PKEY_base_id(pubKey) != EVP_PKEY_RSA) {
    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8081, FALSE,
                                   NULL, NULL, NULL, NULL, NULL);
    EVP_PKEY_free(pubKey);
    X509_free(cert);
    BIO_free(certBio);
    return false;
}

// Verificar tamanho da chave (1024 bits)
int keySize = EVP_PKEY_bits(pubKey);
if (keySize != 1024) {
    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8082, FALSE,
                                   &keySize, NULL, NULL, NULL, NULL);
}

// Guardar referências
m_publicKey = pubKey;  // EVP_PKEY*
m_certificate = cert;   // X509*
m_certBio = certBio;   // BIO*
```

### Fase 4: ThreadMQ.cpp - Assinatura Digital (2-3 horas)

**Código Atual (CryptLib):**
```cpp
cryptCreateSignature(signature, maxSignatureLength, &signatureLength,
                     m_cryptPrivateContext, hashValue, hashLength);
```

**Novo Código OpenSSL:**
```cpp
#include <openssl/evp.h>
#include <openssl/rsa.h>

// Criar contexto de assinatura
EVP_MD_CTX* mdCtx = EVP_MD_CTX_new();
if (!mdCtx) return false;

// Inicializar para assinatura (SHA-256 com RSA)
if (EVP_DigestSignInit(mdCtx, NULL, EVP_sha256(), NULL, m_privateKey) != 1) {
    EVP_MD_CTX_free(mdCtx);
    return false;
}

// Adicionar dados a assinar
if (EVP_DigestSignUpdate(mdCtx, hashValue, hashLength) != 1) {
    EVP_MD_CTX_free(mdCtx);
    return false;
}

// Obter tamanho da assinatura
size_t signatureLength = 0;
if (EVP_DigestSignFinal(mdCtx, NULL, &signatureLength) != 1) {
    EVP_MD_CTX_free(mdCtx);
    return false;
}

// Criar assinatura
unsigned char* signature = new unsigned char[signatureLength];
if (EVP_DigestSignFinal(mdCtx, signature, &signatureLength) != 1) {
    delete[] signature;
    EVP_MD_CTX_free(mdCtx);
    return false;
}

// Limpar
EVP_MD_CTX_free(mdCtx);

// signature contém a assinatura digital
// signatureLength contém o tamanho
```

### Fase 5: ThreadMQ.cpp - Verificação de Assinatura

**Novo Código OpenSSL:**
```cpp
// Verificar assinatura
EVP_MD_CTX* mdCtx = EVP_MD_CTX_new();
if (!mdCtx) return false;

// Inicializar para verificação
if (EVP_DigestVerifyInit(mdCtx, NULL, EVP_sha256(), NULL, m_publicKey) != 1) {
    EVP_MD_CTX_free(mdCtx);
    return false;
}

// Adicionar dados originais
if (EVP_DigestVerifyUpdate(mdCtx, originalData, dataLength) != 1) {
    EVP_MD_CTX_free(mdCtx);
    return false;
}

// Verificar assinatura
int result = EVP_DigestVerifyFinal(mdCtx, signature, signatureLength);
EVP_MD_CTX_free(mdCtx);

if (result == 1) {
    // Assinatura válida
    return true;
} else {
    // Assinatura inválida
    unsigned long err = ERR_get_error();
    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8090, FALSE,
                                   &err, NULL, NULL, NULL, NULL);
    return false;
}
```

---

## 🔧 Mudanças Necessárias em ThreadMQ.h

**Antes (CryptLib):**
```cpp
class CThreadMQ {
private:
    CRYPT_KEYSET m_cryptKeyset;
    CRYPT_CONTEXT m_cryptPublicContext;
    CRYPT_CONTEXT m_cryptPrivateContext;
    CRYPT_CONTEXT m_cryptContext;
    CRYPT_CONTEXT m_crypthashContext;
    int m_cryptstatus;
};
```

**Depois (OpenSSL):**
```cpp
#include <openssl/evp.h>
#include <openssl/x509.h>

class CThreadMQ {
private:
    EVP_PKEY* m_publicKey;        // Chave pública
    EVP_PKEY* m_privateKey;       // Chave privada
    X509* m_certificate;          // Certificado X.509
    BIO* m_certBio;              // BIO para arquivo
    BIO* m_keyBio;               // BIO para chave
};
```

---

## 📦 Dependências

### Remover:
- ❌ CL32.lib (16KB)
- ❌ CL32.dll (672KB)
- ❌ #include <cryptlib.h>

### Adicionar:
- ✅ **Já presente:** libcrypto-3.dll (3.3MB)
- ✅ **Já presente:** libssl-3.dll (701KB)
- ✅ Headers OpenSSL: `<openssl/evp.h>`, `<openssl/x509.h>`, `<openssl/pem.h>`

---

## ⚙️ CMakeLists.txt - Atualizar Linking

**Antes:**
```cmake
# Link CryptLib
target_link_libraries(BCSrvSqlMq PRIVATE
    ${CMAKE_SOURCE_DIR}/CL32.lib
)
```

**Depois:**
```cmake
# Link OpenSSL
find_package(OpenSSL REQUIRED)
target_link_libraries(BCSrvSqlMq PRIVATE
    OpenSSL::Crypto
    OpenSSL::SSL
)
```

---

## ✅ Benefícios da Migração

1. **64-bit Nativo** 🚀
   - Compilação x64 sem problemas
   - Acesso a mais de 2GB de RAM
   - Performance melhorada

2. **Moderno e Seguro** 🔒
   - OpenSSL 3.6.1 (2024)
   - Algoritmos modernos (SHA-256, RSA-2048+)
   - Patches de segurança ativos

3. **Manutenção** 🛠️
   - Amplamente usado e documentado
   - Comunidade ativa
   - Suporte de longo prazo

4. **Compatibilidade** ✨
   - Padrão da indústria
   - Interoperável com outros sistemas
   - Certificados X.509 padrão

---

## ⏱️ Estimativa de Tempo

- **Fase 1**: 1-2 horas (setup)
- **Fase 2**: 30 min (InitSrv.cpp)
- **Fase 3**: 2-3 horas (carregar certificados)
- **Fase 4**: 2-3 horas (assinatura)
- **Fase 5**: 1-2 horas (verificação)
- **Testes**: 2-3 horas

**Total: 9-14 horas** de desenvolvimento

---

## 🎯 Próximos Passos

1. **Revisar** este documento
2. **Decidir** se quer prosseguir
3. **Criar branch** para migração
4. **Implementar** fase por fase
5. **Testar** cada fase
6. **Compilar x64** quando completo

---

Data: 27/02/2026
Autor: Claude Code
Versão: 1.0
