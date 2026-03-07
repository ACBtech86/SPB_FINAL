# Análise: Migração CryptLib → OpenSSL

**Data:** 22/02/2026
**Status:** Análise inicial
**Escopo:** 132 chamadas cryptlib em 9 arquivos

---

## 📊 Estatísticas

| Métrica | Valor |
|---------|-------|
| Total de chamadas cryptlib | 132 |
| Arquivos afetados | 9 (.cpp) + 1 (.h) |
| Funções cryptlib únicas | ~20 |
| Arquivo principal | ThreadMQ.cpp (~100 chamadas) |
| Estimativa de tempo | 20-30 horas |

---

## 📁 Arquivos Afetados

### Headers
- **ThreadMQ.h** - Declarações de variáveis membro crypt*

### Sources
1. **ThreadMQ.cpp** - ~100 chamadas (principal)
2. **InitSrv.cpp** - 4 chamadas (init/end)
3. **BacenRep.cpp** - Include apenas
4. **BacenREQ.cpp** - Include apenas
5. **BacenRSP.cpp** - Include apenas
6. **BacenSup.cpp** - Include apenas
7. **IFREP.cpp** - Include apenas
8. **IFREQ.cpp** - Include apenas
9. **IFRSP.cpp** - Include apenas
10. **IFSUP.cpp** - Include apenas
11. **MainSrv.cpp** - Include apenas
12. **Monitor.cpp** - Include apenas

---

## 🔍 Funções CryptLib Usadas

### Inicialização/Finalização
```cpp
cryptInit()          // Inicializar biblioteca
cryptEnd()           // Finalizar biblioteca
cryptStatusError()   // Verificar erros
```

### Gerenciamento de Keysets
```cpp
cryptKeysetOpen()    // Abrir keyset (arquivo ou ODBC)
cryptKeysetClose()   // Fechar keyset
cryptGetPublicKey()  // Obter chave pública
cryptGetPrivateKey() // Obter chave privada
```

### Contextos
```cpp
cryptCreateContext()        // Criar contexto de criptografia
cryptDestroyContext()       // Destruir contexto
cryptSetAttribute()         // Definir atributo de contexto
cryptGetAttribute()         // Obter atributo de contexto
cryptGetAttributeString()   // Obter atributo string
```

### Operações Criptográficas
```cpp
cryptEncrypt()         // Criptografar dados
cryptDecrypt()         // Descriptografar dados
cryptCheckSignature()  // Verificar assinatura digital
```

---

## 🔄 Mapeamento CryptLib → OpenSSL

### 1. Tipos de Dados

| CryptLib | OpenSSL |
|----------|---------|
| `CRYPT_KEYSET` | `EVP_PKEY*` (chave) ou estrutura personalizada |
| `CRYPT_CONTEXT` | `EVP_CIPHER_CTX*` (cifra) ou `EVP_MD_CTX*` (hash) |
| `CRYPT_UNUSED` | `NULL` |
| Status codes (int) | OpenSSL error codes (int) |

### 2. Inicialização/Finalização

**CryptLib:**
```cpp
int cryptStatus = cryptInit();
if (cryptStatusError(cryptStatus)) { ... }

cryptEnd();
```

**OpenSSL:**
```cpp
// OpenSSL 3.0+ não requer inicialização explícita global
// Mas podemos adicionar para compatibilidade:
OPENSSL_init_crypto(OPENSSL_INIT_LOAD_CONFIG, NULL);

// Cleanup (opcional em OpenSSL 3.0+):
OPENSSL_cleanup();
```

### 3. Keyset Management

**CryptLib:**
```cpp
CRYPT_KEYSET keyset;
cryptKeysetOpen(&keyset, CRYPT_UNUSED, CRYPT_KEYSET_FILE,
                "keyfile.p15", CRYPT_KEYOPT_READONLY);

CRYPT_CONTEXT pubContext;
cryptGetPublicKey(keyset, &pubContext, CRYPT_KEYID_NAME, "keyname");

cryptKeysetClose(keyset);
```

**OpenSSL:**
```cpp
// Carregar chave de arquivo PEM/DER
FILE* fp = fopen("keyfile.pem", "r");
EVP_PKEY* pkey = PEM_read_PrivateKey(fp, NULL, NULL, NULL);
fclose(fp);

// Ou para chave pública:
EVP_PKEY* pubkey = PEM_read_PUBKEY(fp, NULL, NULL, NULL);

// Cleanup:
EVP_PKEY_free(pkey);
```

### 4. Encryption/Decryption

**CryptLib:**
```cpp
CRYPT_CONTEXT ctx;
cryptCreateContext(&ctx, CRYPT_UNUSED, CRYPT_ALGO_AES);
cryptSetAttributeString(ctx, CRYPT_CTXINFO_KEY, key, keylen);
cryptSetAttributeString(ctx, CRYPT_CTXINFO_IV, iv, ivlen);

cryptEncrypt(ctx, data, datalen);
cryptEncrypt(ctx, NULL, 0); // Finalize

cryptDestroyContext(ctx);
```

**OpenSSL:**
```cpp
EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv);

int len;
EVP_EncryptUpdate(ctx, output, &len, input, inputlen);
int ciphertext_len = len;

EVP_EncryptFinal_ex(ctx, output + len, &len);
ciphertext_len += len;

EVP_CIPHER_CTX_free(ctx);
```

### 5. Digital Signatures

**CryptLib:**
```cpp
cryptCheckSignature(signature, publicContext, hashContext);
```

**OpenSSL:**
```cpp
EVP_MD_CTX* mdctx = EVP_MD_CTX_new();
EVP_DigestVerifyInit(mdctx, NULL, EVP_sha256(), NULL, pubkey);
EVP_DigestVerifyUpdate(mdctx, data, datalen);
int result = EVP_DigestVerifyFinal(mdctx, signature, siglen);
EVP_MD_CTX_free(mdctx);
```

---

## 🎯 Estratégia de Migração

### Fase 1: Preparação (2-3 horas)
1. ✅ Análise completa (este documento)
2. ⏸️ Backup de todos os arquivos
3. ⏸️ Criar branch git para migração
4. ⏸️ Estudar formato dos keysets atuais (.p15 files?)

### Fase 2: Headers (1-2 horas)
1. ⏸️ Atualizar ThreadMQ.h
   - Substituir `CRYPT_*` types por `EVP_*` equivalentes
   - Remover `#include "cryptlib.h"`
   - Adicionar `#include <openssl/...>`

2. ⏸️ Atualizar demais arquivos .cpp
   - Remover `#include "cryptlib.h"`
   - Adicionar includes OpenSSL necessários

### Fase 3: InitSrv.cpp (1 hora)
1. ⏸️ Migrar `cryptInit()` → OpenSSL init
2. ⏸️ Migrar `cryptEnd()` → OpenSSL cleanup
3. ⏸️ Testar compilação parcial

### Fase 4: ThreadMQ.cpp - Keyset Management (4-6 horas)
1. ⏸️ Migrar `OpenPublicKey()` function
   - `cryptKeysetOpen()` → arquivo PEM/DER loading
   - `cryptGetPublicKey()` → OpenSSL key parsing
   - Atributos (serial number, algo, keysize)

2. ⏸️ Migrar `OpenPrivateKey()` function
   - Similar ao público mas com senha

### Fase 5: ThreadMQ.cpp - Encryption/Decryption (6-8 horas)
1. ⏸️ Identificar algoritmos usados (AES? RSA? 3DES?)
2. ⏸️ Migrar funções que usam `cryptEncrypt()`
3. ⏸️ Migrar funções que usam `cryptDecrypt()`
4. ⏸️ Ajustar buffer sizes e padding

### Fase 6: ThreadMQ.cpp - Signatures (2-3 horas)
1. ⏸️ Migrar `cryptCheckSignature()`
2. ⏸️ Ajustar formatos de hash

### Fase 7: Cleanup e Destruidores (1-2 horas)
1. ⏸️ Migrar todos `cryptDestroyContext()`
2. ⏸️ Verificar memory leaks
3. ⏸️ RAII wrappers se necessário

### Fase 8: Compilação e Testes (4-6 horas)
1. ⏸️ Resolver erros de compilação
2. ⏸️ Testes unitários das funções crypto
3. ⏸️ Testes de integração
4. ⏸️ Validação com dados reais

---

## ⚠️ Desafios Conhecidos

### 1. Formato de Keysets
- **Problema:** CryptLib usa formato .p15 (PKCS#15?)
- **Solução:** Pode precisar converter para PEM/DER
- **Investigar:** Como as chaves são armazenadas atualmente?

### 2. Compatibilidade de Algoritmos
- **Problema:** CryptLib e OpenSSL podem ter parâmetros diferentes
- **Solução:** Garantir mesmo algoritmo, modo, padding
- **Crítico:** Dados criptografados existentes devem continuar funcionando

### 3. Error Handling
- **Problema:** CryptLib usa `cryptStatusError()` uniformemente
- **Solução:** OpenSSL usa ERR_get_error() e códigos de retorno variados
- **Implementar:** Helper function para padronizar

### 4. Thread Safety
- **Problema:** Múltiplas threads usando crypto
- **Solução:** OpenSSL 3.0+ é thread-safe, mas verificar inicializações

### 5. ODBC Keyset
- **Problema:** `CRYPT_KEYSET_ODBC` não tem equivalente direto
- **Solução:** Implementar carregamento custom de chaves do DB
- **Complexo:** Pode adicionar 4-8 horas ao projeto

---

## 📝 Notas de Implementação

### Includes Necessários (OpenSSL 3.x)
```cpp
#include <openssl/evp.h>        // High-level crypto
#include <openssl/pem.h>        // PEM file handling
#include <openssl/err.h>        // Error handling
#include <openssl/rsa.h>        // RSA (se necessário)
#include <openssl/aes.h>        // AES (se necessário)
#include <openssl/bio.h>        // I/O abstractions
#include <openssl/x509.h>       // Certificates (se necessário)
```

### Helper Functions Recomendadas
```cpp
// Error handling wrapper
bool OpenSSLStatusOK(int status);
std::string GetOpenSSLError();

// RAII wrapper para contextos
class OpenSSLCipherContext {
    EVP_CIPHER_CTX* ctx;
public:
    OpenSSLCipherContext() : ctx(EVP_CIPHER_CTX_new()) {}
    ~OpenSSLCipherContext() { EVP_CIPHER_CTX_free(ctx); }
    EVP_CIPHER_CTX* get() { return ctx; }
};
```

---

## 🔗 Referências

### OpenSSL Documentação
- **OpenSSL 3.0 Wiki:** https://wiki.openssl.org/index.php/OpenSSL_3.0
- **EVP Documentation:** https://www.openssl.org/docs/man3.0/man7/evp.html
- **Migration Guide:** https://www.openssl.org/docs/man3.0/man7/migration_guide.html

### CryptLib
- **Manual:** https://www.cs.auckland.ac.nz/~pgut001/cryptlib/
- **PKCS#15:** https://en.wikipedia.org/wiki/PKCS_15

---

## ✅ Checklist de Validação

Antes de considerar a migração completa:

- [ ] Todas as 132 chamadas cryptlib migradas
- [ ] Código compila sem erros
- [ ] Código compila sem warnings crypto-relacionados
- [ ] Testes unitários de crypto passam
- [ ] Pode carregar chaves públicas e privadas
- [ ] Pode criptografar dados
- [ ] Pode descriptografar dados previamente criptografados
- [ ] Pode verificar assinaturas digitais
- [ ] Sem memory leaks (Valgrind/Dr. Memory)
- [ ] Performance aceitável (comparar com cryptlib)
- [ ] Documentação atualizada

---

**Próximo passo:** Decidir se continuar com migração completa ou abordar o problema cryptlib de outra forma.

**Opções:**
1. **Migração completa OpenSSL** (20-30h) - Resolve definitivamente
2. **Isolar cryptlib temporariamente** (<1h) - Permite testar MSXML
3. **Usar cryptlib em modo compatível** (2-4h) - Resolver conflitos wincrypt.h

