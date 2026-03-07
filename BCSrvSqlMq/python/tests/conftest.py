# conftest.py - Shared fixtures for all tests

import os
import sys
import tempfile
import shutil
import configparser

import pytest

# Ensure bcsrvsqlmq package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temporary directory that is cleaned up after the test."""
    return tmp_path


@pytest.fixture
def sample_ini(tmp_path):
    """Create a sample BCSrvSqlMq.ini file for testing."""
    ini_path = tmp_path / 'BCSrvSqlMq.ini'
    config = configparser.ConfigParser()

    config['Servico'] = {
        'ServiceName': 'TestService',
        'Trace': 'D',
        'MonitorPort': '15000',
        'SrvTimeout': '60',
        'MaxLenMsg': '4096',
    }
    config['Diretorios'] = {
        'DirTraces': str(tmp_path / 'Traces'),
        'DirAudFile': str(tmp_path / 'AuditFiles'),
    }
    config['DataBase'] = {
        'DBServer': 'localhost',
        'DBAliasName': 'testdb',
        'DBName': 'testdb',
        'DBPort': '5432',
        'DBUserName': 'testuser',
        'DBPassword': 'testpass',
        'DbTbControle': 'spb_controle',
        'DbTbStrLog': 'spb_log_bacen',
        'DbTbBacenCidadeApp': 'spb_bacen_to_local',
        'DbTbCidadeBacenApp': 'spb_local_to_bacen',
    }
    config['MQSeries'] = {
        'MQServer': 'localhost',
        'QueueManager': 'QM.TEST.01',
        'QueueTimeout': '10',
        'QLBacenCidadeReq': 'QL.TEST.ENTRADA.BACEN',
        'QLBacenCidadeRsp': 'QL.TEST.SAIDA.BACEN',
        'QLBacenCidadeRep': 'QL.TEST.REPORT.BACEN',
        'QLBacenCidadeSup': 'QL.TEST.SUPORTE.BACEN',
        'QRCidadeBacenReq': 'QR.TEST.ENTRADA.BACEN',
        'QRCidadeBacenRsp': 'QR.TEST.SAIDA.BACEN',
        'QRCidadeBacenRep': 'QR.TEST.REPORT.BACEN',
        'QRCidadeBacenSup': 'QR.TEST.SUPORTE.BACEN',
        'QLIFCidadeReq': 'QL.TEST.ENTRADA.IF',
        'QLIFCidadeRsp': 'QL.TEST.SAIDA.IF',
        'QLIFCidadeRep': 'QL.TEST.REPORT.IF',
        'QLIFCidadeSup': 'QL.TEST.SUPORTE.IF',
        'QRCidadeIFReq': 'QR.TEST.ENTRADA.IF',
        'QRCidadeIFRsp': 'QR.TEST.SAIDA.IF',
        'QRCidadeIFRep': 'QR.TEST.REPORT.IF',
        'QRCidadeIFSup': 'QR.TEST.SUPORTE.IF',
    }
    config['E-Mail'] = {
        'ServerEmail': 'smtp.test.com',
        'SenderEmail': 'test@test.com',
        'SenderName': 'Test',
        'DestEmail': 'admin@test.com',
        'DestName': 'Admin',
    }
    config['Security'] = {
        'UnicodeEnable': 'S',
        'SecurityEnable': 'N',
        'SecurityDB': 'Public Keys',
        'CertificateFile': '',
        'PrivateKeyFile': '',
        'PublicKeyLabel': '',
        'PrivateKeyLabel': '',
        'KeyPassword': '',
    }

    with open(ini_path, 'w', encoding='latin-1') as f:
        config.write(f)

    return ini_path


@pytest.fixture
def rsa_keypair(tmp_path):
    """Generate a self-signed RSA key pair for crypto tests."""
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.x509 import (
        CertificateBuilder, Name, NameAttribute,
        BasicConstraints,
    )
    from cryptography.x509.oid import NameOID
    from datetime import datetime, timedelta

    # Generate RSA key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Write private key PEM
    key_path = tmp_path / 'private.key'
    with open(key_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Create self-signed certificate
    subject = issuer = Name([
        NameAttribute(NameOID.COMMON_NAME, 'Test Certificate'),
    ])
    cert = (
        CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(1000)
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(private_key, hashes.SHA256())
    )

    cert_path = tmp_path / 'public_cert.pem'
    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return str(key_path), str(cert_path), private_key, cert
