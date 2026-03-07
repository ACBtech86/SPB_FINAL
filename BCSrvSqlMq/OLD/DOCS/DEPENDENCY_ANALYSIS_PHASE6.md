# Análise de Dependências - Fase 6: Modernização de Bibliotecas

**Data:** 22/02/2026
**Versão do Projeto:** 1.0.5
**Objetivo:** Substituir bibliotecas legadas (MSXML COM, CryptLib 2001) por bibliotecas modernas (pugixml, OpenSSL)

---

## Resumo Executivo

O projeto BCSrvSqlMq utiliza duas bibliotecas externas críticas:

1. **MSXML (Microsoft XML Parser)** - Via COM (#import)
   - Versão: MSXML 3.0/4.0 (circa 2001)
   - Tecnologia: COM (Component Object Model)
   - Uso: Parse e manipulação de mensagens XML do SPB

2. **CryptLib** - Biblioteca de criptografia
   - Versão: CL32.lib (2001)
   - Algoritmos: RSA 1024, 3DES, MD5, SHA-1
   - Uso: Assinatura digital, verificação, cifragem/decifragem

**Problemas identificados:**
- ❌ Dependências de tecnologias legadas (COM)
- ❌ Algoritmos obsoletos (MD5, 3DES)
- ❌ Falta de manutenção (bibliotecas de 2001)
- ❌ Dificuldade de build em sistemas modernos
- ❌ Risco de segurança (algoritmos fracos)

**Solução proposta:**
- ✅ **MSXML → pugixml** (C++ moderno, header-only option, rápido)
- ✅ **CryptLib → OpenSSL** (padrão da indústria, bem mantido, seguro)

---

## 1. Análise de MSXML

### 1.1 Uso Atual

**Localização:**
- **Header:** `ThreadMQ.h:3` - `#import "msxml.dll" named_guids raw_interfaces_only`
- **Arquivos que usam:**
  - `ThreadMQ.h`, `ThreadMQ.cpp`
  - `BacenREQ.cpp`, `BacenRSP.cpp`
  - `IFREQ.cpp`, `IFRSP.cpp`

**Tipos MSXML usados:**
```cpp
MSXML::IXMLDOMDocument*      // Documento XML
MSXML::IXMLDOMNode*          // Nó XML
MSXML::IXMLDOMNodeList*      // Lista de nós
MSXML::IXMLDOMParseError*    // Erro de parse
MSXML::IXMLDOMNamedNodeMap*  // Mapa de atributos
```

**Membros da classe CThreadMQ:**
```cpp
MSXML::IXMLDOMDocument *m_pDomDoc;  // ThreadMQ.h:103
MSXML::IXMLDOMNode*     m_pDomNode; // ThreadMQ.h:104
HRESULT                 m_hr;        // ThreadMQ.h:105
```

**Macros de suporte:**
```cpp
#define CHECKHR(x) {m_hr = x; if (FAILED(m_hr)) goto CleanUp;}  // ThreadMQ.h:15
#define SAFERELEASE(p) {if (p) {(p)->Release(); p = NULL;}}     // ThreadMQ.h:16
```

### 1.2 Operações XML Implementadas

#### 1.2.1 LoadDocumentSync() - Carregar XML de buffer
**Arquivo:** `ThreadMQ.cpp:730-753`
**Assinatura:**
```cpp
HRESULT CThreadMQ::LoadDocumentSync(MSXML::IXMLDOMDocument *pDoc, BSTR pData, ULONG ulLen);
```

**Funcionalidade:**
1. Aloca BSTR a partir do buffer (SysAllocStringLen)
2. Configura parser: async=false, validateOnParse=true
3. Carrega XML via loadXML()
4. Valida se carregou corretamente via CheckLoad()

**Uso típico:**
```cpp
// BacenREQ.cpp:1279
ULONG lenmsg = m_buflen - sizeof(SECHDR);
CHECKHR(LoadDocumentSync(m_pDomDoc, (BSTR) &m_buffermsg[sizeof(SECHDR)], lenmsg));
```

**Equivalente pugixml:**
```cpp
pugi::xml_document doc;
pugi::xml_parse_result result = doc.load_buffer(buffer, size);
if (!result) {
    // Handle error
}
```

---

#### 1.2.2 FindTag() - Buscar elemento XML
**Arquivo:** `ThreadMQ.cpp:551-607`
**Assinatura:**
```cpp
HRESULT CThreadMQ::FindTag(MSXML::IXMLDOMDocument* pDoc, BSTR pwParent, BSTR pwText, BSTR *pwValue);
```

**Funcionalidade:**
1. Busca elementos por nome via getElementsByTagName()
2. Filtra por nome do nó pai (opcional)
3. Retorna o texto do elemento encontrado

**Uso típico:**
```cpp
// BacenREQ.cpp:1288-1291
CString wrk = _T("DOC");
BSTR strwParent = wrk.AllocSysString();
wrk = _T("NUOp");
BSTR strwFind = wrk.AllocSysString();
m_hr = FindTag(m_pDomDoc, strwParent, strwFind, &strwValue);
// Busca: <DOC><NUOp>valor</NUOp></DOC>
```

**Equivalente pugixml:**
```cpp
std::string FindTag(pugi::xml_document& doc, const char* parent, const char* tag) {
    if (parent) {
        pugi::xml_node parent_node = doc.child(parent);
        pugi::xml_node child = parent_node.child(tag);
        return child.text().as_string();
    } else {
        pugi::xml_node node = doc.find_child_by_attribute(tag);
        return node.text().as_string();
    }
}
```

---

#### 1.2.3 SetTag() - Definir texto de elemento
**Arquivo:** `ThreadMQ.cpp:609-641`
**Assinatura:**
```cpp
HRESULT CThreadMQ::SetTag(MSXML::IXMLDOMDocument* pDoc, BSTR pwText, BSTR *pwValue);
```

**Funcionalidade:**
1. Busca elementos por nome via getElementsByTagName()
2. Define o texto do elemento via put_text()
3. Retorna erro se encontrar mais de 1 elemento

**Equivalente pugixml:**
```cpp
void SetTag(pugi::xml_document& doc, const char* tag, const char* value) {
    pugi::xml_node node = doc.find_child_by_attribute(tag);
    if (node) {
        node.text().set(value);
    }
}
```

---

#### 1.2.4 WalkTree() - Percorrer árvore XML (debug)
**Arquivo:** `ThreadMQ.cpp:646-728`
**Assinatura:**
```cpp
HRESULT CThreadMQ::WalkTree(MSXML::IXMLDOMNode* node, int level);
```

**Funcionalidade:**
1. Percorre recursivamente toda a árvore XML
2. Loga nome dos nós, valores e atributos
3. Usado apenas para debug (logs detalhados)

**Equivalente pugixml:**
```cpp
void WalkTree(pugi::xml_node node, int level) {
    // Log node name
    for (pugi::xml_attribute attr : node.attributes()) {
        // Log attributes
    }
    for (pugi::xml_node child : node.children()) {
        WalkTree(child, level + 1);  // Recursive
    }
}
```

---

#### 1.2.5 SaveDocument() - Salvar XML em arquivo
**Arquivo:** `ThreadMQ.cpp:758-770`
**Assinatura:**
```cpp
HRESULT CThreadMQ::SaveDocument(MSXML::IXMLDOMDocument *pDoc, BSTR pBFName);
```

**Funcionalidade:**
1. Salva documento XML em arquivo via save()

**Equivalente pugixml:**
```cpp
void SaveDocument(pugi::xml_document& doc, const char* filename) {
    doc.save_file(filename);
}
```

---

### 1.3 Padrões de Uso Identificados

**Padrão 1: Carregar e buscar tags**
```cpp
// MSXML (atual):
LoadDocumentSync(m_pDomDoc, buffer, len);
FindTag(m_pDomDoc, L"DOC", L"NUOp", &valor);

// pugixml (novo):
pugi::xml_document doc;
doc.load_buffer(buffer, len);
std::string valor = doc.child("DOC").child("NUOp").text().as_string();
```

**Padrão 2: Modificar e salvar**
```cpp
// MSXML (atual):
SetTag(m_pDomDoc, L"Status", &novoValor);
SaveDocument(m_pDomDoc, L"arquivo.xml");

// pugixml (novo):
doc.child("Status").text().set("novoValor");
doc.save_file("arquivo.xml");
```

---

### 1.4 Impacto da Migração MSXML → pugixml

**Vantagens:**
- ✅ **Performance:** pugixml é muito mais rápido que MSXML
- ✅ **Simplicidade:** API moderna em C++, sem COM
- ✅ **Build:** Sem dependências externas (header-only ou static lib)
- ✅ **Cross-platform:** Funciona em qualquer plataforma
- ✅ **Manutenção:** Ativamente mantido (última versão 2024)

**Desvantagens:**
- ⚠️ **Mudança de API:** Requer reescrita das funções XML
- ⚠️ **BSTR handling:** Precisa converter BSTR para std::string

**Esforço estimado:**
- **Linhas a modificar:** ~300 linhas
- **Arquivos afetados:** 6 arquivos (.h/.cpp)
- **Tempo:** 8-12 horas

---

## 2. Análise de CryptLib

### 2.1 Uso Atual

**Localização:**
- **Header:** `cryptlib.h` (1729 linhas)
- **Biblioteca:** `CL32.lib` (linkada no CMakeLists.txt)
- **Arquivos que incluem:**
  - Todos os threads: `BacenREQ.cpp`, `BacenRSP.cpp`, `BacenRep.cpp`, `BacenSup.cpp`, `IFREQ.cpp`, `IFRSP.cpp`, `IFREP.cpp`, `IFSUP.cpp`
  - Core: `MainSrv.cpp`, `InitSrv.cpp`, `Monitor.cpp`, `ThreadMQ.cpp`

**Tipos CryptLib usados:**
```cpp
CRYPT_KEYSET      // Handle para keyset (arquivo de chaves)
CRYPT_CONTEXT     // Handle para contexto criptográfico
```

**Membros da classe CThreadMQ:**
```cpp
CRYPT_KEYSET    m_cryptKeyset;           // ThreadMQ.h:106
CRYPT_CONTEXT   m_cryptPublicContext;    // ThreadMQ.h:107
CRYPT_CONTEXT   m_cryptPrivateContext;   // ThreadMQ.h:108
CRYPT_CONTEXT   m_crypthashContext;      // ThreadMQ.h:109
CRYPT_CONTEXT   m_cryptContext;          // ThreadMQ.h:110
int             m_cryptstatus;           // ThreadMQ.h:111
BYTE            m_cryptSerialNumberPrv[32];  // ThreadMQ.h:112
BYTE            m_cryptSerialNumberPub[32];  // ThreadMQ.h:113
```

### 2.2 Operações Criptográficas Implementadas

#### 2.2.1 ReadPrivatKey() - Carregar chave privada
**Arquivo:** `ThreadMQ.cpp:862-970`
**Assinatura:**
```cpp
int CThreadMQ::ReadPrivatKey();
```

**Funcionalidade:**
1. Abre keyset de arquivo via `cryptKeysetOpen()`
2. Carrega chave privada via `cryptGetPrivateKey()` com password
3. Valida algoritmo (RSA) e tamanho (1024 bits)
4. Extrai serial number do certificado
5. Fecha keyset

**Funções CryptLib usadas:**
```cpp
cryptKeysetOpen(&m_cryptKeyset, CRYPT_UNUSED, CRYPT_KEYSET_FILE, filename, CRYPT_KEYOPT_READONLY);
cryptGetPrivateKey(m_cryptKeyset, &m_cryptPrivateContext, CRYPT_KEYID_NAME, label, password);
cryptKeysetClose(m_cryptKeyset);
cryptSetAttribute(m_cryptPrivateContext, CRYPT_PROPERTY_OWNER, m_dwThreadId);
cryptGetAttribute(m_cryptPrivateContext, CRYPT_CTXINFO_ALGO, &cryptAlgo);
cryptGetAttribute(m_cryptPrivateContext, CRYPT_CTXINFO_KEYSIZE, &cryptKeySize);
cryptGetAttributeString(m_cryptPrivateContext, CRYPT_CTXINFO_LABEL, &label, &len);
cryptGetAttributeString(m_cryptPrivateContext, CRYPT_CERTINFO_SERIALNUMBER, &serial, &len);
```

**Equivalente OpenSSL:**
```cpp
// Carregar chave privada de arquivo PKCS#12 (.pfx)
#include <openssl/pkcs12.h>
#include <openssl/evp.h>

EVP_PKEY* LoadPrivateKey(const char* filename, const char* password) {
    FILE* fp = fopen(filename, "rb");
    PKCS12* p12 = d2i_PKCS12_fp(fp, NULL);
    fclose(fp);

    EVP_PKEY* pkey = NULL;
    X509* cert = NULL;
    PKCS12_parse(p12, password, &pkey, &cert, NULL);
    PKCS12_free(p12);

    // Validar algoritmo RSA
    if (EVP_PKEY_id(pkey) != EVP_PKEY_RSA) {
        // Erro: não é RSA
    }

    // Validar tamanho da chave (1024 bits)
    RSA* rsa = EVP_PKEY_get1_RSA(pkey);
    if (RSA_size(rsa) * 8 != 1024) {
        // Erro: tamanho incorreto
    }

    return pkey;
}
```

---

#### 2.2.2 ReadPublicKey() - Carregar chave pública
**Arquivo:** `ThreadMQ.cpp:774-860` (similar a ReadPrivatKey)

**Funcionalidade:**
1. Abre keyset de arquivo
2. Carrega chave pública via `cryptGetPublicKey()`
3. Valida algoritmo (RSA) e tamanho (1024 bits)
4. Extrai serial number do certificado

**Equivalente OpenSSL:**
```cpp
// Carregar chave pública de certificado X.509
#include <openssl/x509.h>

EVP_PKEY* LoadPublicKey(const char* filename) {
    FILE* fp = fopen(filename, "rb");
    X509* cert = d2i_X509_fp(fp, NULL);
    fclose(fp);

    EVP_PKEY* pkey = X509_get_pubkey(cert);

    // Validação similar

    return pkey;
}
```

---

#### 2.2.3 funcAssinar() - Assinatura digital RSA
**Arquivo:** `ThreadMQ.cpp:972-1089`
**Assinatura:**
```cpp
int CThreadMQ::funcAssinar(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg);
```

**Funcionalidade:**
1. Cria contexto de hash (MD5 ou SHA-1) baseado em `lpSecHeader->AlgHash`
2. Faz hash dos dados em blocos de 8 bytes (padding se necessário)
3. Finaliza hash com `cryptEncrypt(ctx, msg, 0)`
4. Carrega chave privada (se ainda não carregada)
5. Copia serial number da chave para header
6. Cria assinatura RSA via `cryptCreateSignatureEx()` no formato SPB
7. Copia assinatura (128 bytes) para `lpSecHeader->IniHashCifrSign`

**Algoritmos:**
- **Hash:** MD5 (0x01) ou SHA-1 (0x02)
- **Assinatura:** RSA 1024 bits
- **Formato:** CRYPT_FORMAT_SPB (formato customizado Bacen)

**Fluxo:**
```
msg (dados) → Hash (MD5/SHA) → RSA Sign (chave privada) → assinatura (128 bytes)
```

**Funções CryptLib usadas:**
```cpp
cryptCreateContext(&m_crypthashContext, CRYPT_UNUSED, CRYPT_ALGO_MD5);  // ou CRYPT_ALGO_SHA
cryptSetAttribute(m_crypthashContext, CRYPT_PROPERTY_OWNER, m_dwThreadId);
cryptEncrypt(m_crypthashContext, msg+offset, 8);  // Hash em blocos
cryptEncrypt(m_crypthashContext, msg, 0);  // Finalizar hash
cryptCreateSignatureEx(signature, &len, CRYPT_FORMAT_SPB, m_cryptPrivateContext, m_crypthashContext, CRYPT_USE_DEFAULT);
```

**Equivalente OpenSSL:**
```cpp
#include <openssl/evp.h>
#include <openssl/rsa.h>
#include <openssl/sha.h>
#include <openssl/md5.h>

int funcAssinar(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg, EVP_PKEY* privkey) {
    // 1. Criar contexto de hash
    EVP_MD_CTX* md_ctx = EVP_MD_CTX_new();
    const EVP_MD* md;

    if (lpSecHeader->AlgHash == 0x01) {
        md = EVP_md5();  // MD5
    } else if (lpSecHeader->AlgHash == 0x02) {
        md = EVP_sha1();  // SHA-1
    }

    // 2. Calcular hash
    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int hash_len;

    EVP_DigestInit_ex(md_ctx, md, NULL);
    EVP_DigestUpdate(md_ctx, msg, lentmp);
    EVP_DigestFinal_ex(md_ctx, hash, &hash_len);

    // 3. Assinar hash com RSA
    unsigned char signature[256];
    size_t sig_len = sizeof(signature);

    EVP_PKEY_CTX* pkey_ctx = EVP_PKEY_CTX_new(privkey, NULL);
    EVP_PKEY_sign_init(pkey_ctx);
    EVP_PKEY_sign(pkey_ctx, signature, &sig_len, hash, hash_len);

    // 4. Copiar assinatura para header (formato SPB: 128 bytes)
    memcpy(&lpSecHeader->IniHashCifrSign, signature, 128);

    // Cleanup
    EVP_MD_CTX_free(md_ctx);
    EVP_PKEY_CTX_free(pkey_ctx);

    return 0;  // Success
}
```

---

#### 2.2.4 funcVerifyAss() - Verificação de assinatura
**Arquivo:** `ThreadMQ.cpp:1239-1361`
**Assinatura:**
```cpp
int CThreadMQ::funcVerifyAss(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg);
```

**Funcionalidade:**
1. Cria contexto de hash (MD5 ou SHA-1)
2. Calcula hash dos dados
3. Carrega chave pública (se não carregada)
4. Verifica serial number do certificado
5. Verifica assinatura via `cryptCheckSignatureEx()`

**Fluxo:**
```
msg (dados) → Hash (MD5/SHA) → RSA Verify (chave pública) → OK/ERRO
```

**Funções CryptLib usadas:**
```cpp
cryptCreateContext(&m_crypthashContext, CRYPT_UNUSED, CRYPT_ALGO_MD5/SHA);
cryptEncrypt(m_crypthashContext, msg, lentmp);  // Hash
cryptEncrypt(m_crypthashContext, msg, 0);  // Finalizar
cryptCheckSignatureEx(signature, len, CRYPT_FORMAT_SPB, m_cryptPublicContext, m_crypthashContext);
```

**Equivalente OpenSSL:**
```cpp
int funcVerifyAss(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg, EVP_PKEY* pubkey) {
    // 1. Calcular hash
    EVP_MD_CTX* md_ctx = EVP_MD_CTX_new();
    const EVP_MD* md = (lpSecHeader->AlgHash == 0x01) ? EVP_md5() : EVP_sha1();

    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int hash_len;

    EVP_DigestInit_ex(md_ctx, md, NULL);
    EVP_DigestUpdate(md_ctx, msg, lentmp);
    EVP_DigestFinal_ex(md_ctx, hash, &hash_len);

    // 2. Verificar assinatura
    unsigned char signature[128];
    memcpy(signature, &lpSecHeader->IniHashCifrSign, 128);

    EVP_PKEY_CTX* pkey_ctx = EVP_PKEY_CTX_new(pubkey, NULL);
    EVP_PKEY_verify_init(pkey_ctx);

    int result = EVP_PKEY_verify(pkey_ctx, signature, 128, hash, hash_len);

    // Cleanup
    EVP_MD_CTX_free(md_ctx);
    EVP_PKEY_CTX_free(pkey_ctx);

    return (result == 1) ? 0 : -1;  // 0 = sucesso, -1 = erro
}
```

---

#### 2.2.5 funcCript() - Criptografia (3DES + RSA)
**Arquivo:** `ThreadMQ.cpp:1097-1237`
**Assinatura:**
```cpp
int CThreadMQ::funcCript(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg);
```

**Funcionalidade:**
1. Cria contexto 3DES em modo CBC
2. Gera chave simétrica 3DES aleatória
3. Carrega chave pública RSA (destinatário)
4. Cifra a chave 3DES com a chave pública RSA via `cryptExportKeyEx()`
5. Copia chave cifrada (128 bytes) para `lpSecHeader->IniSymKeyCifr`
6. Cifra os dados com a chave 3DES em blocos de 8 bytes
7. Padding automático se necessário

**Fluxo:**
```
Gera chave 3DES → Cifra chave com RSA público → Cifra dados com 3DES
```

**Funções CryptLib usadas:**
```cpp
cryptCreateContext(&m_cryptContext, CRYPT_UNUSED, CRYPT_ALGO_3DES);
cryptSetAttribute(m_cryptContext, CRYPT_CTXINFO_MODE, CRYPT_MODE_CBC);
cryptGenerateKey(m_cryptContext);  // Gera chave 3DES aleatória
cryptExportKeyEx(encryptedKey, &len, CRYPT_FORMAT_SPB, m_cryptPublicContext, m_cryptContext);  // Cifra chave com RSA
cryptEncrypt(m_cryptContext, msg+offset, 8);  // Cifra dados em blocos
```

**Equivalente OpenSSL:**
```cpp
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/des.h>

int funcCript(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg, EVP_PKEY* pubkey) {
    // 1. Gerar chave 3DES aleatória (24 bytes = 192 bits)
    unsigned char des_key[24];
    unsigned char iv[8];  // IV para modo CBC
    RAND_bytes(des_key, sizeof(des_key));
    RAND_bytes(iv, sizeof(iv));

    // 2. Cifrar chave 3DES com RSA público
    unsigned char encrypted_key[256];
    size_t enc_key_len = sizeof(encrypted_key);

    EVP_PKEY_CTX* pkey_ctx = EVP_PKEY_CTX_new(pubkey, NULL);
    EVP_PKEY_encrypt_init(pkey_ctx);
    EVP_PKEY_encrypt(pkey_ctx, encrypted_key, &enc_key_len, des_key, sizeof(des_key));

    // Copiar chave cifrada para header (128 bytes)
    memcpy(&lpSecHeader->IniSymKeyCifr, encrypted_key, 128);

    // 3. Cifrar dados com 3DES-CBC
    EVP_CIPHER_CTX* cipher_ctx = EVP_CIPHER_CTX_new();
    EVP_EncryptInit_ex(cipher_ctx, EVP_des_ede3_cbc(), NULL, des_key, iv);

    int out_len;
    unsigned char* out_buf = (unsigned char*)malloc(lentmp + 16);  // Buffer com padding
    EVP_EncryptUpdate(cipher_ctx, out_buf, &out_len, msg, lentmp);

    int final_len;
    EVP_EncryptFinal_ex(cipher_ctx, out_buf + out_len, &final_len);

    // Copiar dados cifrados de volta
    memcpy(msg, out_buf, out_len + final_len);
    lentmp = out_len + final_len;

    // Cleanup
    free(out_buf);
    EVP_CIPHER_CTX_free(cipher_ctx);
    EVP_PKEY_CTX_free(pkey_ctx);

    return 0;
}
```

---

#### 2.2.6 funcDeCript() - Decriptografia (3DES + RSA)
**Arquivo:** `ThreadMQ.cpp:1369-1516`
**Assinatura:**
```cpp
int CThreadMQ::funcDeCript(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg);
```

**Funcionalidade:**
1. Cria contexto 3DES em modo CBC
2. Carrega chave privada RSA
3. Verifica serial number do certificado
4. Decifra a chave 3DES usando chave privada RSA via `cryptImportKeyEx()`
5. Decifra os dados com a chave 3DES em blocos de 8 bytes
6. Valida que dados têm tamanho múltiplo de 8

**Fluxo:**
```
Decifra chave com RSA privado → Decifra dados com 3DES
```

**Funções CryptLib usadas:**
```cpp
cryptCreateContext(&m_cryptContext, CRYPT_UNUSED, CRYPT_ALGO_3DES);
cryptSetAttribute(m_cryptContext, CRYPT_CTXINFO_MODE, CRYPT_MODE_CBC);
cryptImportKeyEx(encryptedKey, m_cryptPrivateContext, m_cryptContext);  // Decifra chave com RSA
cryptDecrypt(m_cryptContext, msg+offset, 8);  // Decifra dados em blocos
```

**Equivalente OpenSSL:**
```cpp
int funcDeCript(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg, EVP_PKEY* privkey) {
    // 1. Decifrar chave 3DES com RSA privado
    unsigned char encrypted_key[128];
    memcpy(encrypted_key, &lpSecHeader->IniSymKeyCifr, 128);

    unsigned char des_key[256];
    size_t des_key_len = sizeof(des_key);

    EVP_PKEY_CTX* pkey_ctx = EVP_PKEY_CTX_new(privkey, NULL);
    EVP_PKEY_decrypt_init(pkey_ctx);
    EVP_PKEY_decrypt(pkey_ctx, des_key, &des_key_len, encrypted_key, 128);

    // 2. Decifrar dados com 3DES-CBC
    unsigned char iv[8] = {0};  // IV deve ser o mesmo usado na cifragem

    EVP_CIPHER_CTX* cipher_ctx = EVP_CIPHER_CTX_new();
    EVP_DecryptInit_ex(cipher_ctx, EVP_des_ede3_cbc(), NULL, des_key, iv);

    int out_len;
    unsigned char* out_buf = (unsigned char*)malloc(lentmp);
    EVP_DecryptUpdate(cipher_ctx, out_buf, &out_len, msg, lentmp);

    int final_len;
    EVP_DecryptFinal_ex(cipher_ctx, out_buf + out_len, &final_len);

    // Copiar dados decifrados
    memcpy(msg, out_buf, out_len + final_len);
    lentmp = out_len + final_len;

    // Cleanup
    free(out_buf);
    EVP_CIPHER_CTX_free(cipher_ctx);
    EVP_PKEY_CTX_free(pkey_ctx);

    return 0;
}
```

---

### 2.3 Resumo de Algoritmos Criptográficos

| Operação | Algoritmo Atual | Status Segurança | Alternativa Moderna |
|----------|----------------|------------------|---------------------|
| **Hash** | MD5 (CRYPT_ALGO_MD5) | ❌ INSEGURO (quebrado desde 2004) | SHA-256, SHA-3 |
| **Hash** | SHA-1 (CRYPT_ALGO_SHA) | ⚠️ FRACO (deprecado desde 2017) | SHA-256, SHA-3 |
| **Assinatura** | RSA 1024 bits | ⚠️ FRACO (NIST recomenda 2048+) | RSA 2048/3072, ECDSA |
| **Cifragem Simétrica** | 3DES-CBC | ⚠️ LEGADO (lento, 112-bit security) | AES-256-GCM |
| **Cifragem Assimétrica** | RSA 1024 | ⚠️ FRACO | RSA 2048+, ECDH |

**⚠️ IMPORTANTE:** A migração para OpenSSL permite manter compatibilidade com algoritmos legados (para interoperabilidade com sistemas existentes do Bacen) mas também permite adicionar suporte a algoritmos modernos para futuras atualizações.

---

### 2.4 Impacto da Migração CryptLib → OpenSSL

**Vantagens:**
- ✅ **Segurança:** Biblioteca mais segura e ativamente auditada
- ✅ **Performance:** OpenSSL é altamente otimizado (AES-NI, etc.)
- ✅ **Manutenção:** Ativamente mantido pela comunidade
- ✅ **Flexibilidade:** Suporta todos os algoritmos (legados e modernos)
- ✅ **Padrão da indústria:** Usado em 99% dos sistemas criptográficos
- ✅ **Documentação:** Extensa e atualizada
- ✅ **Compatibilidade:** Funciona em Windows/Linux/macOS

**Desvantagens:**
- ⚠️ **API complexa:** OpenSSL tem API mais verbosa
- ⚠️ **Formato de chaves:** Precisa converter chaves CryptLib → OpenSSL (PKCS#12, PEM)
- ⚠️ **CRYPT_FORMAT_SPB:** Formato customizado Bacen precisa ser mapeado

**Esforço estimado:**
- **Linhas a modificar:** ~800 linhas (funções criptográficas)
- **Arquivos afetados:** 12 arquivos
- **Conversão de chaves:** Necessário converter keysets CryptLib para PKCS#12
- **Tempo:** 20-30 horas

---

## 3. Plano de Migração

### 3.1 Ordem de Execução

**Fase 6.1: Setup e Preparação** (2-3 horas)
1. Instalar vcpkg (se ainda não instalado)
2. Instalar pugixml via vcpkg
3. Instalar OpenSSL via vcpkg
4. Atualizar CMakeLists.txt com novas dependências
5. Criar backup do código atual

**Fase 6.2: Migração MSXML → pugixml** (8-12 horas)
1. Criar classe wrapper `XmlHelper` com funções equivalentes
2. Substituir m_pDomDoc/m_pDomNode por pugi::xml_document
3. Atualizar ThreadMQ.h - remover #import "msxml.dll"
4. Implementar funções XML com pugixml:
   - LoadDocumentSync() → load_buffer()
   - FindTag() → child().text()
   - SetTag() → child().text().set()
   - WalkTree() → iteração recursiva
   - SaveDocument() → save_file()
5. Atualizar todos os arquivos que usam MSXML
6. Compilar e testar

**Fase 6.3: Migração CryptLib → OpenSSL** (20-30 horas)
1. Criar classe wrapper `CryptoHelper` com funções equivalentes
2. Substituir CRYPT_* types por EVP_* types do OpenSSL
3. Implementar funções criptográficas:
   - ReadPrivatKey() → EVP_PKEY (PKCS#12)
   - ReadPublicKey() → EVP_PKEY (X.509)
   - funcAssinar() → EVP_PKEY_sign()
   - funcVerifyAss() → EVP_PKEY_verify()
   - funcCript() → EVP_EncryptInit/Update/Final
   - funcDeCript() → EVP_DecryptInit/Update/Final
4. **Converter chaves:**
   - Criar script para converter keysets CryptLib para PKCS#12
   - Testar carregamento de chaves
5. Atualizar todos os arquivos que usam CryptLib
6. Compilar e testar
7. **Testes de compatibilidade:**
   - Assinar mensagem com OpenSSL, verificar com sistema Bacen legado
   - Cifrar com OpenSSL, decifrar com sistema legado
   - Validar formato SPB

**Fase 6.4: Testes e Validação** (4-6 horas)
1. Testes unitários para XML parsing
2. Testes unitários para criptografia
3. Testes de integração (mensagens reais SPB)
4. Teste de performance (comparar antes/depois)
5. Validação de segurança

**Fase 6.5: Documentação** (2-3 horas)
1. Criar MODERNIZATION_PHASE6.md
2. Atualizar README.md
3. Documentar processo de conversão de chaves
4. Criar guia de troubleshooting

---

### 3.2 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Incompatibilidade de formato de chaves | Alta | Alto | Criar conversor, testar com chaves reais |
| Diferenças em CRYPT_FORMAT_SPB | Média | Alto | Engenharia reversa do formato, criar testes |
| Quebra de compatibilidade com Bacen | Média | Crítico | Testes extensivos, manter versão legada paralela |
| Performance degradada | Baixa | Médio | Benchmarks, otimização se necessário |
| Problemas de build com OpenSSL | Média | Médio | Usar vcpkg, documentar setup |

---

### 3.3 Critérios de Sucesso

**Compilação:**
- ✅ Projeto compila sem erros
- ✅ Sem warnings relacionados a dependências
- ✅ Build funciona em ambiente limpo (CI/CD)

**Funcionalidade:**
- ✅ XML parsing funciona corretamente
- ✅ Assinatura digital compatível com sistema Bacen
- ✅ Verificação de assinatura funciona
- ✅ Cifragem/decifragem compatível
- ✅ Formato de mensagens SPB preservado

**Performance:**
- ✅ Parse XML ≥ performance MSXML
- ✅ Operações criptográficas ≥ performance CryptLib
- ✅ Sem memory leaks
- ✅ Throughput de mensagens mantido

**Compatibilidade:**
- ✅ Interoperabilidade com sistemas Bacen existentes
- ✅ Formato de chaves suportado
- ✅ Formato de mensagens preservado

---

## 4. Checklist de Implementação

### 4.1 Setup (Fase 6.1)
- [ ] Instalar vcpkg
- [ ] `vcpkg install pugixml:x64-windows`
- [ ] `vcpkg install openssl:x64-windows`
- [ ] Atualizar CMakeLists.txt:
  ```cmake
  find_package(pugixml CONFIG REQUIRED)
  find_package(OpenSSL REQUIRED)
  target_link_libraries(BCSrvSqlMq pugixml OpenSSL::SSL OpenSSL::Crypto)
  ```
- [ ] Criar branch `feature/phase6-modern-libs`
- [ ] Commit backup do código atual

### 4.2 MSXML → pugixml (Fase 6.2)
- [ ] Remover `#import "msxml.dll"` de ThreadMQ.h
- [ ] Adicionar `#include <pugixml.hpp>` em ThreadMQ.h
- [ ] Substituir membros da classe:
  ```cpp
  // REMOVER:
  MSXML::IXMLDOMDocument *m_pDomDoc;
  MSXML::IXMLDOMNode* m_pDomNode;
  HRESULT m_hr;

  // ADICIONAR:
  pugi::xml_document m_xmlDoc;
  pugi::xml_parse_result m_xmlResult;
  ```
- [ ] Implementar funções XML (ThreadMQ.cpp):
  - [ ] LoadDocumentSync()
  - [ ] FindTag()
  - [ ] SetTag()
  - [ ] WalkTree()
  - [ ] SaveDocument()
- [ ] Atualizar BacenREQ.cpp - substituir chamadas MSXML
- [ ] Atualizar BacenRSP.cpp - substituir chamadas MSXML
- [ ] Atualizar IFREQ.cpp - substituir chamadas MSXML
- [ ] Atualizar IFRSP.cpp - substituir chamadas MSXML
- [ ] Compilar: `cmake --build build --config Release`
- [ ] Testar parse de mensagem XML real

### 4.3 CryptLib → OpenSSL (Fase 6.3)
- [ ] Remover `#include "cryptlib.h"` de todos os arquivos
- [ ] Adicionar `#include <openssl/evp.h>` e outros headers OpenSSL
- [ ] Substituir membros da classe:
  ```cpp
  // REMOVER:
  CRYPT_KEYSET m_cryptKeyset;
  CRYPT_CONTEXT m_cryptPublicContext;
  CRYPT_CONTEXT m_cryptPrivateContext;
  CRYPT_CONTEXT m_crypthashContext;
  CRYPT_CONTEXT m_cryptContext;

  // ADICIONAR:
  EVP_PKEY* m_publicKey;
  EVP_PKEY* m_privateKey;
  ```
- [ ] Implementar funções criptográficas (ThreadMQ.cpp):
  - [ ] ReadPrivatKey()
  - [ ] ReadPublicKey()
  - [ ] funcAssinar()
  - [ ] funcVerifyAss()
  - [ ] funcCript()
  - [ ] funcDeCript()
- [ ] Criar conversor de chaves CryptLib → PKCS#12
- [ ] Converter chaves de teste
- [ ] Testar carregamento de chaves
- [ ] Testar assinatura e verificação
- [ ] Testar cifragem e decifragem
- [ ] Validar compatibilidade com formato SPB
- [ ] Compilar: `cmake --build build --config Release`

### 4.4 Testes (Fase 6.4)
- [ ] Teste unitário: XML parse
- [ ] Teste unitário: XML find/set tags
- [ ] Teste unitário: Assinatura RSA
- [ ] Teste unitário: Verificação de assinatura
- [ ] Teste unitário: Cifragem 3DES
- [ ] Teste unitário: Decifragem 3DES
- [ ] Teste de integração: Mensagem completa (parse + crypto)
- [ ] Teste de performance: comparar com versão anterior
- [ ] Teste de memory leak (Valgrind ou similar)
- [ ] Teste de compatibilidade com sistema Bacen (se possível)

### 4.5 Documentação (Fase 6.5)
- [ ] Criar MODERNIZATION_PHASE6.md
- [ ] Atualizar README.md (status da Fase 6)
- [ ] Documentar processo de conversão de chaves
- [ ] Criar guia de troubleshooting
- [ ] Atualizar TECHNICAL_DOCUMENTATION.md

---

## 5. Comandos de Instalação

### 5.1 Instalar vcpkg (se necessário)
```bash
# Clone vcpkg
cd C:\dev
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg

# Bootstrap
.\bootstrap-vcpkg.bat

# Integração com Visual Studio
.\vcpkg integrate install
```

### 5.2 Instalar Bibliotecas
```bash
# pugixml
vcpkg install pugixml:x64-windows

# OpenSSL
vcpkg install openssl:x64-windows

# Verificar instalação
vcpkg list
```

### 5.3 Atualizar CMakeLists.txt
```cmake
# No início do arquivo:
set(CMAKE_TOOLCHAIN_FILE "C:/dev/vcpkg/scripts/buildsystems/vcpkg.cmake")

# Depois de project():
find_package(pugixml CONFIG REQUIRED)
find_package(OpenSSL REQUIRED)

# Em target_link_libraries():
target_link_libraries(BCSrvSqlMq
    pugixml
    OpenSSL::SSL
    OpenSSL::Crypto
    # ... outras libs
)
```

---

## 6. Conversão de Chaves CryptLib → OpenSSL

### 6.1 Formato de Chaves CryptLib
CryptLib usa formato proprietário para keysets. Precisamos extrair as chaves e converter para formatos padrão:

- **Chave Privada:** PKCS#12 (.pfx) ou PEM
- **Chave Pública:** X.509 (.cer) ou PEM

### 6.2 Script de Conversão (Python)
```python
# Nota: Este é um exemplo conceitual
# A conversão real depende do formato exato usado pelo CryptLib

import subprocess

def convert_cryptlib_to_pkcs12(cryptlib_file, password, output_p12):
    """
    Converte keyset CryptLib para PKCS#12 (OpenSSL compatível)

    Passos:
    1. Usar CryptLib CLI (se disponível) para exportar chave
    2. Converter para PEM
    3. Criar PKCS#12 com OpenSSL
    """
    # Exemplo usando OpenSSL CLI
    cmd = f'openssl pkcs12 -export -out {output_p12} -inkey privkey.pem -in cert.pem -passout pass:{password}'
    subprocess.run(cmd, shell=True)

# Uso:
convert_cryptlib_to_pkcs12(
    'BacenPrivate.key',  # Arquivo CryptLib
    'senha123',           # Password
    'BacenPrivate.pfx'   # PKCS#12 output
)
```

### 6.3 Testar Chaves Convertidas
```cpp
// Testar carregamento em OpenSSL
#include <openssl/pkcs12.h>

void TestKeyLoad(const char* pkcs12_file, const char* password) {
    FILE* fp = fopen(pkcs12_file, "rb");
    PKCS12* p12 = d2i_PKCS12_fp(fp, NULL);
    fclose(fp);

    EVP_PKEY* pkey = NULL;
    X509* cert = NULL;

    int result = PKCS12_parse(p12, password, &pkey, &cert, NULL);

    if (result == 1) {
        printf("✅ Chave carregada com sucesso!\n");
        printf("   Tipo: %s\n", EVP_PKEY_id(pkey) == EVP_PKEY_RSA ? "RSA" : "Outro");
        printf("   Tamanho: %d bits\n", EVP_PKEY_bits(pkey));
    } else {
        printf("❌ Erro ao carregar chave\n");
    }

    PKCS12_free(p12);
    EVP_PKEY_free(pkey);
    X509_free(cert);
}
```

---

## 7. Estimativa de Tempo Total

| Fase | Tarefa | Tempo Estimado |
|------|--------|----------------|
| 6.1 | Setup e Preparação | 2-3 horas |
| 6.2 | Migração MSXML → pugixml | 8-12 horas |
| 6.3 | Migração CryptLib → OpenSSL | 20-30 horas |
| 6.4 | Testes e Validação | 4-6 horas |
| 6.5 | Documentação | 2-3 horas |
| **TOTAL** | | **36-54 horas** |

**Estimativa realista:** 5-7 dias de trabalho (1 desenvolvedor full-time)

---

## 8. Notas Finais

### 8.1 Compatibilidade com SPB/Bacen

**CRÍTICO:** O Sistema de Pagamentos Brasileiro (SPB) do Bacen usa formatos e algoritmos específicos. A migração DEVE preservar:

1. **Formato de mensagens XML** - Estrutura exata dos documentos
2. **Formato de assinatura** - CRYPT_FORMAT_SPB precisa ser mapeado
3. **Algoritmos** - Mesmo que legados (MD5, SHA-1, 3DES), manter compatibilidade
4. **Serial numbers** - Formato de certificados deve ser preservado

**Recomendação:** Criar ambiente de testes com mensagens reais do Bacen antes de deploy em produção.

### 8.2 Upgrade de Algoritmos (Futuro)

Após migração bem-sucedida para OpenSSL, considerar upgrade gradual:

| Algoritmo Legado | Algoritmo Moderno | Quando Migrar |
|------------------|-------------------|---------------|
| MD5 | SHA-256 | Após aprovação Bacen |
| SHA-1 | SHA-256/SHA-3 | Após aprovação Bacen |
| RSA 1024 | RSA 2048/3072 | Próxima atualização SPB |
| 3DES-CBC | AES-256-GCM | Próxima versão do protocolo |

### 8.3 Manutenção Futura

Com OpenSSL, futuras atualizações serão mais simples:
- ✅ Suporte a novos algoritmos via updates do OpenSSL
- ✅ Patches de segurança regulares
- ✅ Compatibilidade com TLS 1.3+
- ✅ Suporte a hardware crypto (AES-NI, etc.)

---

**Documento criado em:** 22/02/2026
**Autor:** Claude Sonnet 4.5
**Status:** ✅ Análise completa - Pronto para implementação
