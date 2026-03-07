# test_openssl_wrapper.py - Unit tests for cryptography wrapper

import os
import pytest

from bcsrvsqlmq.security.openssl_wrapper import (
    CryptoContext, DigitalSignature, SymmetricCrypto,
    init_crypto, cleanup_crypto,
)


class TestCryptoContext:
    """Tests for CryptoContext key management."""

    def test_initialize_openssl(self):
        assert CryptoContext.initialize_openssl() is True

    def test_cleanup_openssl(self):
        CryptoContext.cleanup_openssl()  # Should not raise

    def test_load_public_key_from_certificate(self, rsa_keypair):
        key_path, cert_path, _, _ = rsa_keypair
        ctx = CryptoContext()
        assert ctx.load_public_key_from_certificate(cert_path) is True
        assert ctx.m_publicKey is not None
        assert ctx.m_certificate is not None

    def test_load_private_key(self, rsa_keypair):
        key_path, cert_path, _, _ = rsa_keypair
        ctx = CryptoContext()
        assert ctx.load_private_key(key_path) is True
        assert ctx.m_privateKey is not None

    def test_load_bad_cert_path(self, tmp_path):
        ctx = CryptoContext()
        assert ctx.load_public_key_from_certificate(str(tmp_path / 'nonexistent.pem')) is False
        assert ctx.get_last_error() != ''

    def test_load_bad_key_path(self, tmp_path):
        ctx = CryptoContext()
        assert ctx.load_private_key(str(tmp_path / 'nonexistent.key')) is False
        assert ctx.get_last_error() != ''

    def test_get_key_size(self, rsa_keypair):
        key_path, cert_path, _, _ = rsa_keypair
        ctx = CryptoContext()
        ctx.load_public_key_from_certificate(cert_path)
        assert ctx.get_key_size() == 2048

    def test_is_rsa_key(self, rsa_keypair):
        key_path, cert_path, _, _ = rsa_keypair
        ctx = CryptoContext()
        ctx.load_public_key_from_certificate(cert_path)
        assert ctx.is_rsa_key() is True

    def test_cleanup(self, rsa_keypair):
        key_path, cert_path, _, _ = rsa_keypair
        ctx = CryptoContext()
        ctx.load_public_key_from_certificate(cert_path)
        ctx.load_private_key(key_path)
        ctx.cleanup()
        assert ctx.m_publicKey is None
        assert ctx.m_privateKey is None
        assert ctx.m_certificate is None


class TestDigitalSignature:
    """Tests for digital signature operations."""

    def test_sign_and_verify_sha256(self, rsa_keypair):
        key_path, cert_path, private_key, cert = rsa_keypair
        public_key = cert.public_key()

        data = b'Hello, SPB!'
        signature, sig_len = DigitalSignature.create_signature(data, private_key)
        assert signature is not None
        assert sig_len > 0

        assert DigitalSignature.verify_signature(data, signature, public_key) is True

    def test_sign_and_verify_sha1(self, rsa_keypair):
        _, _, private_key, cert = rsa_keypair
        public_key = cert.public_key()

        data = b'Test SHA-1 signature'
        signature, sig_len = DigitalSignature.create_signature(data, private_key, 0x02)
        assert signature is not None

        assert DigitalSignature.verify_signature(data, signature, public_key, 0x02) is True

    def test_sign_and_verify_md5(self, rsa_keypair):
        _, _, private_key, cert = rsa_keypair
        public_key = cert.public_key()

        data = b'Test MD5 signature'
        signature, sig_len = DigitalSignature.create_signature(data, private_key, 0x01)
        assert signature is not None

        assert DigitalSignature.verify_signature(data, signature, public_key, 0x01) is True

    def test_verify_bad_signature(self, rsa_keypair):
        _, _, private_key, cert = rsa_keypair
        public_key = cert.public_key()

        data = b'Original data'
        signature, _ = DigitalSignature.create_signature(data, private_key)

        # Tamper with data
        assert DigitalSignature.verify_signature(b'Tampered', signature, public_key) is False

    def test_verify_cryptlib_header(self, rsa_keypair):
        """Verify signature with legacy CryptLib 3-byte header prefix."""
        _, _, private_key, cert = rsa_keypair
        public_key = cert.public_key()

        data = b'Legacy CryptLib test'
        signature, _ = DigitalSignature.create_signature(data, private_key)

        # Prepend legacy CryptLib header
        legacy_sig = bytes([0x43, 0x81, 0x80]) + signature
        assert DigitalSignature.verify_signature(data, legacy_sig, public_key) is True

    def test_create_signature_no_key(self):
        sig, length = DigitalSignature.create_signature(b'data', None)
        assert sig is None
        assert length == 0


class TestSymmetricCrypto:
    """Tests for Triple-DES encryption/decryption."""

    def test_generate_3des_key(self):
        key = SymmetricCrypto.generate_3des_key()
        assert len(key) == 24

    def test_generate_iv(self):
        iv = SymmetricCrypto.generate_iv()
        assert len(iv) == 8

    def test_encrypt_decrypt_roundtrip(self):
        key = SymmetricCrypto.generate_3des_key()
        iv = SymmetricCrypto.generate_iv()
        plaintext = b'Hello, Triple-DES!'

        encrypted = SymmetricCrypto.encrypt_3des(plaintext, key, iv)
        assert encrypted != plaintext

        decrypted = SymmetricCrypto.decrypt_3des(encrypted, key, iv)
        assert decrypted == plaintext

    def test_encrypt_decrypt_block_aligned(self):
        """Data that's exactly 8 bytes (block size)."""
        key = SymmetricCrypto.generate_3des_key()
        iv = b'\x00' * 8
        plaintext = b'12345678'  # Exactly one block

        encrypted = SymmetricCrypto.encrypt_3des(plaintext, key, iv)
        decrypted = SymmetricCrypto.decrypt_3des(encrypted, key, iv)
        assert decrypted == plaintext

    def test_encrypt_decrypt_large_data(self):
        key = SymmetricCrypto.generate_3des_key()
        iv = SymmetricCrypto.generate_iv()
        plaintext = os.urandom(4096)

        encrypted = SymmetricCrypto.encrypt_3des(plaintext, key, iv)
        decrypted = SymmetricCrypto.decrypt_3des(encrypted, key, iv)
        assert decrypted == plaintext

    def test_wrap_unwrap_key_rsa(self, rsa_keypair):
        _, _, private_key, cert = rsa_keypair
        public_key = cert.public_key()

        des3_key = SymmetricCrypto.generate_3des_key()

        # Wrap with public key
        wrapped = SymmetricCrypto.wrap_key_rsa(des3_key, public_key)
        assert wrapped != des3_key

        # Unwrap with private key
        unwrapped = SymmetricCrypto.unwrap_key_rsa(wrapped, private_key)
        assert unwrapped == des3_key

    def test_full_encrypt_flow(self, rsa_keypair):
        """Test complete flow: generate key, wrap, encrypt, unwrap, decrypt."""
        _, _, private_key, cert = rsa_keypair
        public_key = cert.public_key()

        plaintext = b'SPB message payload data for testing encryption'

        # Sender side
        des3_key = SymmetricCrypto.generate_3des_key()
        iv = SymmetricCrypto.generate_iv()
        encrypted_key = SymmetricCrypto.wrap_key_rsa(des3_key, public_key)
        encrypted_data = SymmetricCrypto.encrypt_3des(plaintext, des3_key, iv)

        # Receiver side
        recovered_key = SymmetricCrypto.unwrap_key_rsa(encrypted_key, private_key)
        decrypted_data = SymmetricCrypto.decrypt_3des(encrypted_data, recovered_key, iv)

        assert decrypted_data == plaintext


class TestInitCleanup:
    """Tests for module-level init/cleanup."""

    def test_init_crypto(self):
        assert init_crypto() is True

    def test_cleanup_crypto(self):
        cleanup_crypto()  # Should not raise
