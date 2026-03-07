#!/usr/bin/env python3
"""
Bacen (Central Bank) Simulator for BCSrvSqlMq.

Simulates the Bacen side of the SPB message exchange on the SAME queue manager.
Uses simulation certificates (bacen_sim.key / finvest_sim.cer) so both sides
can encrypt/decrypt messages locally.

Flows:
  - RECEIVE from Finvest: MQGET from QL.36266751.01.ENTRADA.IF
    (Finvest's CIFReq puts messages here, encrypted with bacen_sim.cer)
    Bacen decrypts with bacen_sim.key, verifies signature with finvest_sim.cer

  - SEND to Finvest: MQPUT to QL.REQ.00038166.36266751.01
    (Finvest's CBacenReq reads from here)
    Bacen signs with bacen_sim.key, encrypts with finvest_sim.cer

Usage:
    python bacen_simulator.py

Prerequisites:
    - IBM MQ queue manager QM.36266751.01 running
    - FINVEST.SVRCONN channel on localhost(1414)
    - Simulation certificates in certificates/ directory
    - pip install pymqi cryptography lxml
"""

import os
import sys
import struct
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CERT_DIR = os.path.join(PROJECT_ROOT, 'certificates')

# Add python/ to path so we can import bcsrvsqlmq modules
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'python'))

import pymqi
import pymqi.CMQC

from bcsrvsqlmq.msg_sgr import (
    SECHDR, SECHDR_SIZE, SECHDR_V1_SIZE,
    ALG_RSA_2048, ALG_3DES_168, ALG_HASH_SHA256,
    SECHDR_VERSION_CLEAR, SECHDR_VERSION_V2, CA_SERPRO,
)
from bcsrvsqlmq.security.openssl_wrapper import (
    CryptoContext, DigitalSignature, SymmetricCrypto,
)

# ---------------------------------------------------------------------------
# MQ Configuration
# ---------------------------------------------------------------------------
QM_NAME = 'QM.36266751.01'
CHANNEL = 'FINVEST.SVRCONN'
CONN_INFO = 'localhost(1414)'

# Queues where Finvest PUTS outbound messages (Bacen reads these)
FINVEST_OUTBOUND_QUEUES = {
    'REQ': 'QL.36266751.01.ENTRADA.IF',
    'RSP': 'QL.36266751.01.SAIDA.IF',
    'REP': 'QL.36266751.01.REPORT.IF',
    'SUP': 'QL.36266751.01.SUPORTE.IF',
}

# Queues where Bacen PUTS inbound messages (Finvest reads these)
FINVEST_INBOUND_QUEUES = {
    'REQ': 'QL.REQ.00038166.36266751.01',
    'RSP': 'QL.RSP.00038166.36266751.01',
    'REP': 'QL.REP.00038166.36266751.01',
    'SUP': 'QL.SUP.00038166.36266751.01',
}

# ---------------------------------------------------------------------------
# Certificate files
# ---------------------------------------------------------------------------
BACEN_PRIVATE_KEY = os.path.join(CERT_DIR, 'bacen_sim.key')
BACEN_CERTIFICATE = os.path.join(CERT_DIR, 'bacen_sim.cer')
FINVEST_CERTIFICATE = os.path.join(CERT_DIR, 'finvest_sim.cer')


# ---------------------------------------------------------------------------
# Crypto helpers
# ---------------------------------------------------------------------------
class BacenCrypto:
    """Handles Bacen-side cryptography."""

    def __init__(self):
        self.bacen_private_key = None
        self.bacen_cert_serial = b'\x00' * 32
        self.finvest_public_key = None
        self.finvest_cert_serial = b'\x00' * 32
        self._loaded = False

    def load_keys(self):
        if self._loaded:
            return True

        # Load Bacen private key (for signing outbound, decrypting inbound)
        ctx = CryptoContext()
        if not ctx.load_private_key(BACEN_PRIVATE_KEY):
            print(f'  ERROR: Cannot load Bacen private key: {BACEN_PRIVATE_KEY}')
            return False
        self.bacen_private_key = ctx.m_privateKey

        # Load Bacen certificate (to get serial number)
        ctx2 = CryptoContext()
        if not ctx2.load_public_key_from_certificate(BACEN_CERTIFICATE):
            print(f'  ERROR: Cannot load Bacen certificate: {BACEN_CERTIFICATE}')
            return False
        serial = ctx2.m_certificate.serial_number
        serial_bytes = serial.to_bytes(32, byteorder='big')
        self.bacen_cert_serial = serial_bytes[-32:]

        # Load Finvest certificate (for encrypting outbound, verifying inbound)
        ctx3 = CryptoContext()
        if not ctx3.load_public_key_from_certificate(FINVEST_CERTIFICATE):
            print(f'  ERROR: Cannot load Finvest certificate: {FINVEST_CERTIFICATE}')
            return False
        self.finvest_public_key = ctx3.m_publicKey
        serial = ctx3.m_certificate.serial_number
        serial_bytes = serial.to_bytes(32, byteorder='big')
        self.finvest_cert_serial = serial_bytes[-32:]

        self._loaded = True
        print('  Crypto keys loaded OK')
        return True

    def decrypt_message(self, sec_hdr: SECHDR, payload: bytes) -> bytes:
        """Decrypt a message received from Finvest (encrypted with Bacen public cert)."""
        if sec_hdr.Versao not in (0x01, 0x02):
            return payload  # clear text

        # 1. Decrypt: unwrap 3DES key with Bacen private key, then decrypt payload
        rsa_size = self.bacen_private_key.key_size // 8  # 128 for 1024, 256 for 2048
        encrypted_key = sec_hdr.SymKeyCifr[:rsa_size]
        des3_key = SymmetricCrypto.unwrap_key_rsa(encrypted_key, self.bacen_private_key)
        iv = b'\x00' * 8
        decrypted = SymmetricCrypto.decrypt_3des(payload, des3_key, iv)

        # 2. Verify signature with Finvest public key
        finvest_rsa_size = self.finvest_public_key.key_size // 8
        signature = sec_hdr.HashCifrSign[:finvest_rsa_size]
        hash_algo = sec_hdr.AlgHash
        if DigitalSignature.verify_signature(decrypted, signature,
                                              self.finvest_public_key, hash_algo):
            print('  Signature: VALID')
        else:
            print('  Signature: INVALID (verification failed)')

        return decrypted

    def encrypt_message(self, payload: bytes) -> tuple:
        """Encrypt a message to send to Finvest.

        Returns (SECHDR, encrypted_payload).
        Sign with Bacen private key, encrypt with Finvest public cert.
        """
        sec_hdr = SECHDR()  # defaults to V2 (588 bytes, RSA-2048, SHA-256)
        sec_hdr.Versao = SECHDR_VERSION_V2
        sec_hdr.CodErro = 0x00
        sec_hdr.AlgAssymKey = ALG_RSA_2048
        sec_hdr.AlgSymKey = ALG_3DES_168
        sec_hdr.AlgAssymKeyLocal = ALG_RSA_2048
        sec_hdr.AlgHash = ALG_HASH_SHA256
        sec_hdr.CADest = CA_SERPRO
        sec_hdr.CALocal = CA_SERPRO

        # Pad to 8-byte alignment (3DES block size)
        pad_len = (8 - (len(payload) % 8)) % 8
        padded = payload + b'\x00' * pad_len

        # 1. Sign with Bacen private key
        signature, sig_len = DigitalSignature.create_signature(
            padded, self.bacen_private_key, ALG_HASH_SHA256)
        if signature is None:
            raise RuntimeError('Signing failed')
        sec_hdr.HashCifrSign = signature[:256].ljust(256, b'\x00')
        sec_hdr.NumSerieCertLocal = self.bacen_cert_serial[:32]

        # 2. Encrypt with Finvest public key (3DES + RSA key wrap)
        des3_key = SymmetricCrypto.generate_3des_key()
        iv = b'\x00' * 8  # SPB spec: zero IV
        encrypted_key = SymmetricCrypto.wrap_key_rsa(des3_key, self.finvest_public_key)
        sec_hdr.SymKeyCifr = encrypted_key[:256].ljust(256, b'\x00')
        sec_hdr.NumSerieCertDest = self.finvest_cert_serial[:32]

        encrypted_payload = SymmetricCrypto.encrypt_3des(padded, des3_key, iv)

        return sec_hdr, encrypted_payload


# ---------------------------------------------------------------------------
# MQ Connection
# ---------------------------------------------------------------------------
def connect_mq():
    """Connect to queue manager via TCP client channel."""
    cd = pymqi.CD()
    cd.ChannelName = CHANNEL.encode()
    cd.ConnectionName = CONN_INFO.encode()
    cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
    cd.TransportType = pymqi.CMQC.MQXPT_TCP
    qm = pymqi.QueueManager(None)
    qm.connect_with_options(QM_NAME, cd)
    return qm


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------
def decode_payload_to_xml(payload: bytes) -> str:
    """Decode UTF-16BE payload to string (matching Finvest's encoding)."""
    # Byte-swap UTF-16BE to UTF-16LE
    swapped = bytearray(len(payload))
    for i in range(0, len(payload) - 1, 2):
        swapped[i] = payload[i + 1]
        swapped[i + 1] = payload[i]
    try:
        text = bytes(swapped).decode('utf-16-le').rstrip('\x00')
        return text
    except UnicodeDecodeError:
        # Fallback: try as raw Latin-1
        return payload.decode('latin-1', errors='replace').rstrip('\x00')


def encode_xml_to_payload(xml_text: str) -> bytes:
    """Encode XML string to UTF-16BE payload (matching Finvest's format)."""
    utf16le = xml_text.encode('utf-16-le')
    # Byte-swap to UTF-16BE
    be = bytearray(len(utf16le))
    for i in range(0, len(utf16le) - 1, 2):
        be[i] = utf16le[i + 1]
        be[i + 1] = utf16le[i]
    return bytes(be)


def build_bacen_xml(cod_msg: str, nu_ope: str, text: str = '') -> str:
    """Build a sample Bacen XML message."""
    now = datetime.now()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<DOC>
  <BCMSG>
    <IdentdEmissor>00038166</IdentdEmissor>
    <IdentdDestinatario>36266751</IdentdDestinatario>
    <IdentdContWorknudo>GEN</IdentdContWorknudo>
    <NUOp>{nu_ope}</NUOp>
    <DtHrMsg>{now.strftime('%Y-%m-%dT%H:%M:%S')}</DtHrMsg>
  </BCMSG>
  <SISMSG>
    <CodMsg>{cod_msg}</CodMsg>
    <NumCtrlIF>BCSIM{nu_ope[-6:]}</NumCtrlIF>
    <NumCtrlSTR>BCSTR{nu_ope[-6:]}</NumCtrlSTR>
  </SISMSG>
  <GENMSG>
    <TxtMsg>{text or f'Bacen simulator message {nu_ope}'}</TxtMsg>
  </GENMSG>
</DOC>"""


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------
def browse_all_queues():
    """Show depth of all relevant queues."""
    print('\n' + '=' * 70)
    print('  QUEUE DEPTHS')
    print('=' * 70)

    qm = connect_mq()
    try:
        all_queues = {}
        all_queues.update({f'[Finvest OUT] {v}': v for v in FINVEST_OUTBOUND_QUEUES.values()})
        all_queues.update({f'[Finvest IN]  {v}': v for v in FINVEST_INBOUND_QUEUES.values()})

        for label, qname in all_queues.items():
            try:
                q = pymqi.Queue(qm, qname, pymqi.CMQC.MQOO_INQUIRE)
                depth = q.inquire(pymqi.CMQC.MQIA_CURRENT_Q_DEPTH)
                q.close()
                marker = ' <<<' if depth > 0 else ''
                print(f'  {label:<55} depth={depth}{marker}')
            except pymqi.MQMIError as e:
                print(f'  {label:<55} ERROR rc={e.reason}')
    finally:
        qm.disconnect()

    print()


def receive_from_finvest(crypto: BacenCrypto):
    """Read messages from Finvest outbound IF queues (Bacen receives)."""
    print('\n' + '=' * 70)
    print('  RECEIVE FROM FINVEST (Bacen reads IF staging queues)')
    print('=' * 70)

    if not crypto.load_keys():
        return

    print('\n  Which queue type?')
    print('  1. REQ (Requests)')
    print('  2. RSP (Responses)')
    print('  3. REP (Reports)')
    print('  4. SUP (Support)')
    print('  0. All queues')
    choice = input('  > ').strip()

    type_map = {'1': 'REQ', '2': 'RSP', '3': 'REP', '4': 'SUP'}
    if choice == '0':
        queues_to_read = list(FINVEST_OUTBOUND_QUEUES.items())
    elif choice in type_map:
        t = type_map[choice]
        queues_to_read = [(t, FINVEST_OUTBOUND_QUEUES[t])]
    else:
        print('  Invalid choice.')
        return

    qm = connect_mq()
    total = 0
    try:
        for msg_type, qname in queues_to_read:
            try:
                q = pymqi.Queue(qm, qname, pymqi.CMQC.MQOO_INPUT_SHARED)
            except pymqi.MQMIError as e:
                print(f'\n  Cannot open {qname}: rc={e.reason}')
                continue

            count = 0
            while True:
                try:
                    md = pymqi.MD()
                    gmo = pymqi.GMO()
                    gmo.Options = (pymqi.CMQC.MQGMO_NO_WAIT |
                                   pymqi.CMQC.MQGMO_FAIL_IF_QUIESCING)
                    raw = q.get(None, md, gmo)
                    count += 1
                    total += 1

                    print(f'\n  --- Message #{total} from {qname} [{msg_type}] ---')
                    print(f'  MsgId:    {md.MsgId.hex()[:48]}')
                    print(f'  CorrelId: {md.CorrelId.hex()[:48]}')
                    print(f'  Length:   {len(raw)} bytes')

                    # Detect header version from first 2 bytes
                    if len(raw) >= 2:
                        hdr_size_val = int.from_bytes(raw[0:2], 'little')
                        if hdr_size_val == SECHDR_V1_SIZE:
                            hdr_size = SECHDR_V1_SIZE
                        else:
                            hdr_size = SECHDR_SIZE
                    else:
                        hdr_size = SECHDR_SIZE

                    if len(raw) >= hdr_size:
                        sec_hdr = SECHDR.unpack(raw[:hdr_size])
                        payload = raw[hdr_size:]

                        print(f'  SECHDR:   size={hdr_size} Versao={sec_hdr.Versao:#04x}'
                              f'  CodErro={sec_hdr.CodErro:#04x}'
                              f'  AlgHash={sec_hdr.AlgHash:#04x}'
                              f'  AlgAssymKey={sec_hdr.AlgAssymKey:#04x}')

                        if sec_hdr.Versao in (0x01, 0x02):
                            print(f'  Security: Encrypted + Signed (V{sec_hdr.Versao})')
                            try:
                                decrypted = crypto.decrypt_message(sec_hdr, payload)
                                xml_text = decode_payload_to_xml(decrypted)
                                print(f'  Decrypted XML ({len(xml_text)} chars):')
                                print()
                                for line in xml_text.split('\n'):
                                    print(f'    {line}')
                                print()
                            except Exception as ex:
                                print(f'  Decryption FAILED: {ex}')
                                print(f'  Raw payload (first 100 bytes): {payload[:100].hex()}')
                        else:
                            print('  Security: Clear text')
                            xml_text = decode_payload_to_xml(payload)
                            print(f'  XML ({len(xml_text)} chars):')
                            print()
                            for line in xml_text.split('\n'):
                                print(f'    {line}')
                            print()
                    else:
                        print(f'  Raw ({len(raw)} bytes): {raw[:200].hex()}')

                except pymqi.MQMIError as e:
                    if e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                        break
                    raise

            q.close()
            if count > 0:
                print(f'  [{msg_type}] Read {count} message(s) from {qname}')

    finally:
        qm.disconnect()

    if total == 0:
        print('\n  No messages available on any queue.')
    else:
        print(f'\n  Total: {total} message(s) received.')


def send_to_finvest(crypto: BacenCrypto):
    """Put a message on Bacen local queues (Finvest reads these)."""
    print('\n' + '=' * 70)
    print('  SEND TO FINVEST (Bacen puts on Bacen local queues)')
    print('=' * 70)

    if not crypto.load_keys():
        return

    print('\n  Which queue type?')
    print('  1. REQ (Request to Finvest)')
    print('  2. RSP (Response to Finvest)')
    print('  3. REP (Report to Finvest)')
    print('  4. SUP (Support to Finvest)')
    choice = input('  > ').strip()

    type_map = {'1': 'REQ', '2': 'RSP', '3': 'REP', '4': 'SUP'}
    if choice not in type_map:
        print('  Invalid choice.')
        return

    msg_type = type_map[choice]
    qname = FINVEST_INBOUND_QUEUES[msg_type]

    # Build message
    now = datetime.now()
    nu_ope = f'{now.strftime("%Y%m%d")}{now.hour:02d}{now.minute:02d}{now.second:02d}'

    print(f'\n  CodMsg (default GEN0014): ', end='')
    cod_msg = input().strip() or 'GEN0014'

    print(f'  NuOpe  (default {nu_ope}): ', end='')
    nu_ope_input = input().strip()
    if nu_ope_input:
        nu_ope = nu_ope_input

    print(f'  Text   (default auto): ', end='')
    text = input().strip()

    print(f'\n  Security mode?')
    print(f'  1. Encrypted + Signed (V2, RSA-2048, SHA-256)')
    print(f'  2. Clear text (Versao=0x00)')
    sec_choice = input('  > ').strip()
    use_security = sec_choice != '2'

    xml_text = build_bacen_xml(cod_msg, nu_ope, text)
    print(f'\n  XML Message:')
    for line in xml_text.split('\n'):
        print(f'    {line}')

    payload = encode_xml_to_payload(xml_text)

    if use_security:
        print(f'\n  Signing with Bacen key + Encrypting with Finvest cert...')
        sec_hdr, encrypted_payload = crypto.encrypt_message(payload)
        mq_msg = sec_hdr.pack() + encrypted_payload
        print(f'  SECHDR: {SECHDR_SIZE} bytes, Payload: {len(encrypted_payload)} bytes')
    else:
        sec_hdr = SECHDR()
        sec_hdr.Versao = SECHDR_VERSION_CLEAR
        mq_msg = sec_hdr.pack() + payload
        print(f'  SECHDR: {SECHDR_SIZE} bytes (clear), Payload: {len(payload)} bytes')

    print(f'  Total message: {len(mq_msg)} bytes')
    print(f'  Target queue: {qname}')

    print(f'\n  Confirm MQPUT? (y/n): ', end='')
    if input().strip().lower() != 'y':
        print('  Cancelled.')
        return

    # MQPUT
    qm = connect_mq()
    try:
        q = pymqi.Queue(qm, qname, pymqi.CMQC.MQOO_OUTPUT)
        md = pymqi.MD()
        md.Format = pymqi.CMQC.MQFMT_NONE
        pmo = pymqi.PMO()
        q.put(mq_msg, md, pmo)
        q.close()
        print(f'\n  MQPUT OK to {qname} ({len(mq_msg)} bytes)')
        print(f'  MsgId: {md.MsgId.hex()[:48]}')
    except pymqi.MQMIError as e:
        print(f'\n  MQPUT FAILED: rc={e.reason}')
    finally:
        qm.disconnect()


def browse_messages():
    """Browse (peek without removing) messages on any queue."""
    print('\n' + '=' * 70)
    print('  BROWSE MESSAGES (peek without removing)')
    print('=' * 70)

    print('\n  Finvest OUTBOUND (Bacen receives):')
    for i, (t, q) in enumerate(FINVEST_OUTBOUND_QUEUES.items(), 1):
        print(f'    {i}. [{t}] {q}')
    print('  Finvest INBOUND (Bacen sends):')
    for i, (t, q) in enumerate(FINVEST_INBOUND_QUEUES.items(), 5):
        print(f'    {i}. [{t}] {q}')

    choice = input('  Queue number> ').strip()
    all_queues = list(FINVEST_OUTBOUND_QUEUES.values()) + list(FINVEST_INBOUND_QUEUES.values())
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(all_queues):
            qname = all_queues[idx]
        else:
            print('  Invalid choice.')
            return
    except ValueError:
        print('  Invalid choice.')
        return

    qm = connect_mq()
    count = 0
    try:
        q = pymqi.Queue(qm, qname, pymqi.CMQC.MQOO_BROWSE)
        while True:
            try:
                md = pymqi.MD()
                gmo = pymqi.GMO()
                gmo.Options = (pymqi.CMQC.MQGMO_BROWSE_NEXT |
                               pymqi.CMQC.MQGMO_NO_WAIT |
                               pymqi.CMQC.MQGMO_FAIL_IF_QUIESCING)
                raw = q.get(None, md, gmo)
                count += 1

                print(f'\n  --- Message #{count} on {qname} ---')
                print(f'  MsgId:  {md.MsgId.hex()[:48]}')
                print(f'  Length: {len(raw)} bytes')

                # Detect header version
                if len(raw) >= 2:
                    hdr_size_val = int.from_bytes(raw[0:2], 'little')
                    hdr_size = SECHDR_V1_SIZE if hdr_size_val == SECHDR_V1_SIZE else SECHDR_SIZE
                else:
                    hdr_size = SECHDR_SIZE

                if len(raw) >= hdr_size:
                    sec_hdr = SECHDR.unpack(raw[:hdr_size])
                    print(f'  SECHDR: size={hdr_size} Versao={sec_hdr.Versao:#04x}'
                          f'  CodErro={sec_hdr.CodErro:#04x}')
                    if sec_hdr.Versao == 0x00:
                        payload = raw[hdr_size:]
                        xml_text = decode_payload_to_xml(payload)
                        print(f'  XML preview: {xml_text[:200]}...')
                else:
                    print(f'  Raw: {raw[:100].hex()}')

                if count >= 10:
                    print(f'\n  (showing first 10 messages)')
                    break

            except pymqi.MQMIError as e:
                if e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                    break
                raise
        q.close()
    except pymqi.MQMIError as e:
        print(f'  Error: rc={e.reason}')
    finally:
        qm.disconnect()

    if count == 0:
        print(f'\n  No messages on {qname}')
    else:
        print(f'\n  {count} message(s) on queue (not removed).')


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------
def main():
    print()
    print('=' * 70)
    print('  BACEN SIMULATOR - Central Bank SPB Message Exchange')
    print('  Queue Manager: ' + QM_NAME)
    print('  Channel:       ' + CHANNEL + ' @ ' + CONN_INFO)
    print('=' * 70)

    # Verify certificate files
    missing = []
    for label, path in [('Bacen private key', BACEN_PRIVATE_KEY),
                         ('Bacen certificate', BACEN_CERTIFICATE),
                         ('Finvest certificate', FINVEST_CERTIFICATE)]:
        if not os.path.exists(path):
            missing.append(f'  MISSING: {label} -> {path}')
    if missing:
        print('\n  Certificate files not found:')
        for m in missing:
            print(m)
        print('\n  Run the keypair generator first (see SESSION_NOTES.md)')
        sys.exit(1)
    else:
        print('\n  Certificates: OK')

    crypto = BacenCrypto()

    while True:
        print('\n  ---- MENU ----')
        print('  1. Browse queue depths')
        print('  2. Receive from Finvest (MQGET from IF staging queues)')
        print('  3. Send to Finvest (MQPUT to Bacen local queues)')
        print('  4. Browse messages (peek without removing)')
        print('  0. Exit')
        print()
        choice = input('  > ').strip()

        try:
            if choice == '1':
                browse_all_queues()
            elif choice == '2':
                receive_from_finvest(crypto)
            elif choice == '3':
                send_to_finvest(crypto)
            elif choice == '4':
                browse_messages()
            elif choice == '0':
                print('\n  Goodbye.')
                break
            else:
                print('  Invalid option.')
        except pymqi.MQMIError as e:
            print(f'\n  MQ Error: comp={e.comp} reason={e.reason}')
        except KeyboardInterrupt:
            print('\n  Interrupted.')
        except Exception as e:
            print(f'\n  Error: {e}')
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
