# openssl_wrapper.py - Cryptography wrapper (port of OpenSSLWrapper.cpp/h)

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509 import load_pem_x509_certificate
from cryptography.exceptions import InvalidSignature
import os


class CryptoContext:
    """Key and certificate management (replaces OpenSSLCrypto::CryptoContext)."""

    def __init__(self):
        self.m_publicKey = None
        self.m_privateKey = None
        self.m_certificate = None
        self._last_error = ''

    @staticmethod
    def initialize_openssl() -> bool:
        # Python's cryptography library auto-initializes
        return True

    @staticmethod
    def cleanup_openssl():
        pass

    def load_public_key_from_certificate(self, cert_path: str) -> bool:
        try:
            with open(cert_path, 'rb') as f:
                pem_data = f.read()
            self.m_certificate = load_pem_x509_certificate(pem_data)
            self.m_publicKey = self.m_certificate.public_key()
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    def load_private_key(self, key_path: str, password: str = None) -> bool:
        try:
            with open(key_path, 'rb') as f:
                pem_data = f.read()
            pwd = password.encode() if password else None
            self.m_privateKey = serialization.load_pem_private_key(pem_data, password=pwd)
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    def get_key_size(self) -> int:
        if self.m_publicKey:
            return self.m_publicKey.key_size
        return 0

    def is_rsa_key(self) -> bool:
        if self.m_publicKey is None:
            return False
        from cryptography.hazmat.primitives.asymmetric import rsa
        return isinstance(self.m_publicKey, rsa.RSAPublicKey)

    def get_last_error(self) -> str:
        return self._last_error

    def cleanup(self):
        self.m_publicKey = None
        self.m_privateKey = None
        self.m_certificate = None


class DigitalSignature:
    """Digital signature operations (replaces OpenSSLCrypto::DigitalSignature)."""

    _last_error = ''

    @staticmethod
    def create_signature(data: bytes, private_key, digest_algo=None) -> tuple:
        """Create digital signature.

        Args:
            data: Data to sign
            private_key: RSA private key
            digest_algo: Hash algorithm (0x01=MD5, 0x02=SHA-1, None=SHA-256)

        Returns:
            (signature_bytes, length) or (None, 0) on failure
        """
        try:
            hash_algo = DigitalSignature._get_hash_algo(digest_algo)
            signature = private_key.sign(data, asym_padding.PKCS1v15(), hash_algo)
            return signature, len(signature)
        except Exception as e:
            DigitalSignature._last_error = str(e)
            return None, 0

    @staticmethod
    def verify_signature(data: bytes, signature: bytes, public_key,
                         digest_algo=None) -> bool:
        """Verify digital signature.

        Args:
            data: Original data
            signature: Signature to verify
            public_key: RSA public key
            digest_algo: Hash algorithm (0x01=MD5, 0x02=SHA-1, None=SHA-256)

        Returns:
            True if signature is valid
        """
        try:
            # Handle legacy CryptLib 3-byte header (0x43, 0x81, 0x80)
            if len(signature) > 3 and signature[:3] == bytes([0x43, 0x81, 0x80]):
                signature = signature[3:]

            hash_algo = DigitalSignature._get_hash_algo(digest_algo)
            public_key.verify(signature, data, asym_padding.PKCS1v15(), hash_algo)
            return True
        except InvalidSignature:
            DigitalSignature._last_error = 'Signature verification failed'
            return False
        except Exception as e:
            DigitalSignature._last_error = str(e)
            return False

    @staticmethod
    def _get_hash_algo(digest_algo):
        if digest_algo == 0x01:
            return hashes.MD5()
        elif digest_algo == 0x02:
            return hashes.SHA1()
        elif digest_algo == 0x03:
            return hashes.SHA256()
        else:
            return hashes.SHA256()  # default to SHA-256

    @staticmethod
    def get_last_error() -> str:
        return DigitalSignature._last_error


class SymmetricCrypto:
    """Symmetric encryption operations (Triple-DES + RSA key wrapping)."""

    @staticmethod
    def encrypt_3des(data: bytes, key: bytes, iv: bytes) -> bytes:
        """Encrypt data using Triple-DES CBC mode.

        Args:
            data: Plaintext data (will be PKCS7 padded)
            key: 24-byte Triple-DES key
            iv: 8-byte initialization vector

        Returns:
            Encrypted data
        """
        # PKCS7 padding to 8-byte blocks
        pad_len = 8 - (len(data) % 8)
        padded_data = data + bytes([pad_len] * pad_len)

        cipher = Cipher(algorithms.TripleDES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        return encryptor.update(padded_data) + encryptor.finalize()

    @staticmethod
    def decrypt_3des(data: bytes, key: bytes, iv: bytes) -> bytes:
        """Decrypt Triple-DES CBC encrypted data.

        Args:
            data: Encrypted data
            key: 24-byte Triple-DES key
            iv: 8-byte initialization vector

        Returns:
            Decrypted data (PKCS7 unpadded)
        """
        cipher = Cipher(algorithms.TripleDES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(data) + decryptor.finalize()

        # Remove PKCS7 padding
        if padded:
            pad_len = padded[-1]
            if 0 < pad_len <= 8 and all(b == pad_len for b in padded[-pad_len:]):
                return padded[:-pad_len]
        return padded

    @staticmethod
    def wrap_key_rsa(des3_key: bytes, public_key) -> bytes:
        """RSA-encrypt the Triple-DES key."""
        return public_key.encrypt(des3_key, asym_padding.PKCS1v15())

    @staticmethod
    def unwrap_key_rsa(encrypted_key: bytes, private_key) -> bytes:
        """RSA-decrypt the Triple-DES key."""
        return private_key.decrypt(encrypted_key, asym_padding.PKCS1v15())

    @staticmethod
    def generate_3des_key() -> bytes:
        """Generate a random 24-byte Triple-DES key."""
        return os.urandom(24)

    @staticmethod
    def generate_iv() -> bytes:
        """Generate a random 8-byte IV for CBC mode."""
        return os.urandom(8)


def init_crypto() -> bool:
    return CryptoContext.initialize_openssl()


def cleanup_crypto():
    CryptoContext.cleanup_openssl()
