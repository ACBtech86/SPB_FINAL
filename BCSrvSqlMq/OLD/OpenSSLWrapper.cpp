/*
 * OpenSSLWrapper.cpp
 *
 * Implementação do wrapper OpenSSL 3.6.1
 *
 * Criado: 27/02/2026
 */

#include "OpenSSLWrapper.h"
#include <cstring>
#include <sstream>

namespace OpenSSLCrypto {

// ===========================================================================
// Variáveis estáticas
// ===========================================================================
char DigitalSignature::s_lastError[512] = {0};

// ===========================================================================
// CryptoContext - Implementação
// ===========================================================================

CryptoContext::CryptoContext()
    : m_publicKey(nullptr)
    , m_privateKey(nullptr)
    , m_certificate(nullptr)
    , m_certBio(nullptr)
    , m_keyBio(nullptr)
{
    memset(m_lastError, 0, sizeof(m_lastError));
}

CryptoContext::~CryptoContext()
{
    Cleanup();
}

bool CryptoContext::InitializeOpenSSL()
{
    // OpenSSL 3.x auto-inicializa, mas vamos garantir
    OpenSSL_add_all_algorithms();
    ERR_load_crypto_strings();
    return true;
}

void CryptoContext::CleanupOpenSSL()
{
    EVP_cleanup();
    ERR_free_strings();
}

bool CryptoContext::LoadPublicKeyFromCertificate(const char* certPath)
{
    if (!certPath) {
        SetLastError("Certificate path is null");
        return false;
    }

    // Abrir arquivo do certificado
    m_certBio = BIO_new_file(certPath, "r");
    if (!m_certBio) {
        SetLastErrorFromOpenSSL();
        return false;
    }

    // Ler certificado X.509
    m_certificate = PEM_read_bio_X509(m_certBio, nullptr, nullptr, nullptr);
    if (!m_certificate) {
        SetLastErrorFromOpenSSL();
        BIO_free(m_certBio);
        m_certBio = nullptr;
        return false;
    }

    // Extrair chave pública do certificado
    m_publicKey = X509_get_pubkey(m_certificate);
    if (!m_publicKey) {
        SetLastErrorFromOpenSSL();
        return false;
    }

    return true;
}

bool CryptoContext::LoadPrivateKey(const char* keyPath, const char* password)
{
    if (!keyPath) {
        SetLastError("Key path is null");
        return false;
    }

    // Abrir arquivo da chave
    m_keyBio = BIO_new_file(keyPath, "r");
    if (!m_keyBio) {
        SetLastErrorFromOpenSSL();
        return false;
    }

    // Ler chave privada (com ou sem senha)
    m_privateKey = PEM_read_bio_PrivateKey(
        m_keyBio,
        nullptr,
        nullptr,  // Callback para senha (nullptr = usar password)
        const_cast<char*>(password)
    );

    if (!m_privateKey) {
        SetLastErrorFromOpenSSL();
        BIO_free(m_keyBio);
        m_keyBio = nullptr;
        return false;
    }

    return true;
}

int CryptoContext::GetKeySize() const
{
    if (!m_publicKey) {
        return 0;
    }
    return EVP_PKEY_bits(m_publicKey);
}

bool CryptoContext::IsRSAKey() const
{
    if (!m_publicKey) {
        return false;
    }
    return EVP_PKEY_base_id(m_publicKey) == EVP_PKEY_RSA;
}

const char* CryptoContext::GetLastError() const
{
    return m_lastError;
}

void CryptoContext::Cleanup()
{
    if (m_publicKey) {
        EVP_PKEY_free(m_publicKey);
        m_publicKey = nullptr;
    }

    if (m_privateKey) {
        EVP_PKEY_free(m_privateKey);
        m_privateKey = nullptr;
    }

    if (m_certificate) {
        X509_free(m_certificate);
        m_certificate = nullptr;
    }

    if (m_certBio) {
        BIO_free(m_certBio);
        m_certBio = nullptr;
    }

    if (m_keyBio) {
        BIO_free(m_keyBio);
        m_keyBio = nullptr;
    }
}

void CryptoContext::SetLastError(const char* error)
{
    if (error) {
        strncpy_s(m_lastError, sizeof(m_lastError), error, _TRUNCATE);
    }
}

void CryptoContext::SetLastErrorFromOpenSSL()
{
    unsigned long err = ERR_get_error();
    if (err != 0) {
        char buf[256];
        ERR_error_string_n(err, buf, sizeof(buf));
        SetLastError(buf);
    } else {
        SetLastError("Unknown OpenSSL error");
    }
}

// ===========================================================================
// DigitalSignature - Implementação
// ===========================================================================

bool DigitalSignature::CreateSignature(
    const unsigned char* data,
    size_t dataLength,
    EVP_PKEY* privateKey,
    unsigned char** signature,
    size_t* signatureLength,
    const EVP_MD* digestAlgo)
{
    if (!data || !privateKey || !signature || !signatureLength) {
        SetLastError("Invalid parameters");
        return false;
    }

    // Usar SHA-256 como padrão
    if (!digestAlgo) {
        digestAlgo = EVP_sha256();
    }

    // Criar contexto de digest
    EVP_MD_CTX* mdCtx = EVP_MD_CTX_new();
    if (!mdCtx) {
        SetLastErrorFromOpenSSL();
        return false;
    }

    // Inicializar para assinatura
    if (EVP_DigestSignInit(mdCtx, nullptr, digestAlgo, nullptr, privateKey) != 1) {
        SetLastErrorFromOpenSSL();
        EVP_MD_CTX_free(mdCtx);
        return false;
    }

    // Adicionar dados
    if (EVP_DigestSignUpdate(mdCtx, data, dataLength) != 1) {
        SetLastErrorFromOpenSSL();
        EVP_MD_CTX_free(mdCtx);
        return false;
    }

    // Obter tamanho necessário
    size_t sigLen = 0;
    if (EVP_DigestSignFinal(mdCtx, nullptr, &sigLen) != 1) {
        SetLastErrorFromOpenSSL();
        EVP_MD_CTX_free(mdCtx);
        return false;
    }

    // Alocar buffer para assinatura
    *signature = new unsigned char[sigLen];
    *signatureLength = sigLen;

    // Criar assinatura
    if (EVP_DigestSignFinal(mdCtx, *signature, signatureLength) != 1) {
        SetLastErrorFromOpenSSL();
        delete[] *signature;
        *signature = nullptr;
        *signatureLength = 0;
        EVP_MD_CTX_free(mdCtx);
        return false;
    }

    EVP_MD_CTX_free(mdCtx);
    return true;
}

bool DigitalSignature::VerifySignature(
    const unsigned char* data,
    size_t dataLength,
    const unsigned char* signature,
    size_t signatureLength,
    EVP_PKEY* publicKey,
    const EVP_MD* digestAlgo)
{
    if (!data || !signature || !publicKey) {
        SetLastError("Invalid parameters");
        return false;
    }

    // Usar SHA-256 como padrão
    if (!digestAlgo) {
        digestAlgo = EVP_sha256();
    }

    // Criar contexto de digest
    EVP_MD_CTX* mdCtx = EVP_MD_CTX_new();
    if (!mdCtx) {
        SetLastErrorFromOpenSSL();
        return false;
    }

    // Inicializar para verificação
    if (EVP_DigestVerifyInit(mdCtx, nullptr, digestAlgo, nullptr, publicKey) != 1) {
        SetLastErrorFromOpenSSL();
        EVP_MD_CTX_free(mdCtx);
        return false;
    }

    // Adicionar dados
    if (EVP_DigestVerifyUpdate(mdCtx, data, dataLength) != 1) {
        SetLastErrorFromOpenSSL();
        EVP_MD_CTX_free(mdCtx);
        return false;
    }

    // Verificar assinatura
    int result = EVP_DigestVerifyFinal(mdCtx, signature, signatureLength);
    EVP_MD_CTX_free(mdCtx);

    if (result == 1) {
        return true;  // Assinatura válida
    } else if (result == 0) {
        SetLastError("Signature verification failed");
        return false;  // Assinatura inválida
    } else {
        SetLastErrorFromOpenSSL();
        return false;  // Erro durante verificação
    }
}

const char* DigitalSignature::GetLastError()
{
    return s_lastError;
}

void DigitalSignature::SetLastError(const char* error)
{
    if (error) {
        strncpy_s(s_lastError, sizeof(s_lastError), error, _TRUNCATE);
    }
}

void DigitalSignature::SetLastErrorFromOpenSSL()
{
    unsigned long err = ERR_get_error();
    if (err != 0) {
        char buf[256];
        ERR_error_string_n(err, buf, sizeof(buf));
        SetLastError(buf);
    } else {
        SetLastError("Unknown OpenSSL error");
    }
}

// ===========================================================================
// Funções auxiliares globais
// ===========================================================================

bool InitCrypto()
{
    return CryptoContext::InitializeOpenSSL();
}

void CleanupCrypto()
{
    CryptoContext::CleanupOpenSSL();
}

std::string GetOpenSSLError()
{
    unsigned long err = ERR_get_error();
    if (err == 0) {
        return "No error";
    }

    char buf[256];
    ERR_error_string_n(err, buf, sizeof(buf));
    return std::string(buf);
}

} // namespace OpenSSLCrypto
