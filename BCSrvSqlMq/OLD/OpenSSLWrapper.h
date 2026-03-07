/*
 * OpenSSLWrapper.h
 *
 * Wrapper para facilitar o uso do OpenSSL 3.6.1
 * Substitui funcionalidade do CryptLib (CL32.dll)
 *
 * Criado: 27/02/2026
 * Propósito: Migração CryptLib → OpenSSL para compilação x64
 */

#pragma once

#include <openssl/evp.h>
#include <openssl/x509.h>
#include <openssl/pem.h>
#include <openssl/bio.h>
#include <openssl/err.h>
#include <openssl/rsa.h>
#include <string>

namespace OpenSSLCrypto {

// ===========================================================================
// Classe para gerenciamento de chaves e certificados
// ===========================================================================
class CryptoContext {
public:
    CryptoContext();
    ~CryptoContext();

    // Inicialização global do OpenSSL
    static bool InitializeOpenSSL();
    static void CleanupOpenSSL();

    // Carregar certificado (chave pública) de arquivo PEM
    bool LoadPublicKeyFromCertificate(const char* certPath);

    // Carregar chave privada de arquivo PEM
    bool LoadPrivateKey(const char* keyPath, const char* password = nullptr);

    // Obter informações da chave
    int GetKeySize() const;           // Em bits
    bool IsRSAKey() const;
    const char* GetLastError() const;

    // Getters para uso interno
    EVP_PKEY* GetPublicKey() const { return m_publicKey; }
    EVP_PKEY* GetPrivateKey() const { return m_privateKey; }
    X509* GetCertificate() const { return m_certificate; }

    // Liberar recursos
    void Cleanup();

private:
    EVP_PKEY* m_publicKey;
    EVP_PKEY* m_privateKey;
    X509* m_certificate;
    BIO* m_certBio;
    BIO* m_keyBio;

    mutable char m_lastError[512];

    void SetLastError(const char* error);
    void SetLastErrorFromOpenSSL();
};

// ===========================================================================
// Funções de assinatura digital
// ===========================================================================
class DigitalSignature {
public:
    // Criar assinatura digital
    static bool CreateSignature(
        const unsigned char* data,          // Dados a assinar
        size_t dataLength,                  // Tamanho dos dados
        EVP_PKEY* privateKey,              // Chave privada
        unsigned char** signature,          // [OUT] Assinatura (alocada aqui)
        size_t* signatureLength,           // [OUT] Tamanho da assinatura
        const EVP_MD* digestAlgo = nullptr // Algoritmo hash (default: SHA-256)
    );

    // Verificar assinatura digital
    static bool VerifySignature(
        const unsigned char* data,          // Dados originais
        size_t dataLength,                  // Tamanho dos dados
        const unsigned char* signature,     // Assinatura a verificar
        size_t signatureLength,            // Tamanho da assinatura
        EVP_PKEY* publicKey,               // Chave pública
        const EVP_MD* digestAlgo = nullptr // Algoritmo hash (default: SHA-256)
    );

    // Obter último erro
    static const char* GetLastError();

private:
    static char s_lastError[512];
    static void SetLastError(const char* error);
    static void SetLastErrorFromOpenSSL();
};

// ===========================================================================
// Funções auxiliares
// ===========================================================================

// Inicializar biblioteca OpenSSL (chamar no início do programa)
bool InitCrypto();

// Limpar recursos OpenSSL (chamar no fim do programa)
void CleanupCrypto();

// Obter mensagem de erro legível do OpenSSL
std::string GetOpenSSLError();

} // namespace OpenSSLCrypto
