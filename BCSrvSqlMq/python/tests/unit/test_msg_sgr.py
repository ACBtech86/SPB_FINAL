# test_msg_sgr.py - Unit tests for binary message structures

import struct
import pytest

from bcsrvsqlmq.msg_sgr import (
    COMHDR, COMHDR_SIZE, COMHDR_FORMAT,
    SECHDR, SECHDR_SIZE, SECHDR_FORMAT,
    STAUDITFILE, STTASKSTATUS, MIMSG,
    MAXMSGLENGTH, MINMSGLENGTH,
    TASKS_COUNT, FUNC_POST, FUNC_NOP,
)


class TestCOMHDR:
    """Tests for the 11-byte COMHDR communication header."""

    def test_size_is_11_bytes(self):
        assert COMHDR_SIZE == 11

    def test_default_values(self):
        hdr = COMHDR()
        assert hdr.usMsgLength == 0
        assert hdr.ucIdHeader == b'\x00' * 4
        assert hdr.ucFuncSgr == 0
        assert hdr.usRc == 0
        assert hdr.usDatLength == 0

    def test_pack_unpack_roundtrip(self):
        hdr = COMHDR(
            usMsgLength=256,
            ucIdHeader=b'TEST',
            ucFuncSgr=FUNC_POST,
            usRc=0,
            usDatLength=100,
        )
        packed = hdr.pack()
        assert len(packed) == COMHDR_SIZE

        restored = COMHDR.unpack(packed)
        assert restored.usMsgLength == 256
        assert restored.ucIdHeader == b'TEST'
        assert restored.ucFuncSgr == FUNC_POST
        assert restored.usRc == 0
        assert restored.usDatLength == 100

    def test_pack_little_endian(self):
        hdr = COMHDR(usMsgLength=0x0102, ucIdHeader=b'ABCD',
                      ucFuncSgr=0xFF, usRc=0x0304, usDatLength=0x0506)
        packed = hdr.pack()
        # Little-endian: 0x0102 -> 02 01
        assert packed[0] == 0x02
        assert packed[1] == 0x01

    def test_func_nop_value(self):
        hdr = COMHDR(ucFuncSgr=FUNC_NOP)
        packed = hdr.pack()
        restored = COMHDR.unpack(packed)
        assert restored.ucFuncSgr == 0xFF

    def test_unpack_with_extra_data(self):
        """Unpack should work even if data has trailing bytes."""
        hdr = COMHDR(usMsgLength=42, ucIdHeader=b'HEAD')
        packed = hdr.pack() + b'\x00' * 100
        restored = COMHDR.unpack(packed)
        assert restored.usMsgLength == 42
        assert restored.ucIdHeader == b'HEAD'

    def test_max_values(self):
        hdr = COMHDR(usMsgLength=0xFFFF, ucFuncSgr=0xFF,
                      usRc=0xFFFF, usDatLength=0xFFFF)
        packed = hdr.pack()
        restored = COMHDR.unpack(packed)
        assert restored.usMsgLength == 0xFFFF
        assert restored.usRc == 0xFFFF
        assert restored.usDatLength == 0xFFFF


class TestSECHDR:
    """Tests for the 332-byte SECHDR security header."""

    def test_size_is_332_bytes(self):
        assert SECHDR_SIZE == 332

    def test_default_values(self):
        sec = SECHDR()
        assert sec.Versao == 0
        assert sec.CodErro == 0
        assert sec.AlgHash == 0

    def test_pack_unpack_roundtrip(self):
        sec = SECHDR(
            TamSecHeader=struct.pack('<H', SECHDR_SIZE),
            Versao=1,
            CodErro=0,
            AlgAssymKey=1,
            AlgSymKey=1,
            AlgHash=2,
            CADest=1,
            NumSerieCertDest=b'\x01' * 32,
            CALocal=2,
            NumSerieCertLocal=b'\x02' * 32,
            SymKeyCifr=b'\xAA' * 127,
            HashCifrSign=b'\xBB' * 127,
        )
        packed = sec.pack()
        assert len(packed) == SECHDR_SIZE

        restored = SECHDR.unpack(packed)
        assert restored.Versao == 1
        assert restored.AlgHash == 2
        assert restored.CADest == 1
        assert restored.NumSerieCertDest == b'\x01' * 32
        assert restored.NumSerieCertLocal == b'\x02' * 32
        assert restored.SymKeyCifr == b'\xAA' * 127
        assert restored.HashCifrSign == b'\xBB' * 127

    def test_clear_version_zero(self):
        """Version 0x00 means cleartext (no security)."""
        sec = SECHDR(Versao=0)
        packed = sec.pack()
        restored = SECHDR.unpack(packed)
        assert restored.Versao == 0

    def test_algorithm_constants(self):
        from bcsrvsqlmq.msg_sgr import ALG_RSA_1024, ALG_3DES_168, ALG_HASH_MD5, ALG_HASH_SHA1
        assert ALG_RSA_1024 == 0x01
        assert ALG_3DES_168 == 0x01
        assert ALG_HASH_MD5 == 0x01
        assert ALG_HASH_SHA1 == 0x02


class TestSTAUDITFILE:
    """Tests for the audit file record structure."""

    def test_pack_unpack_roundtrip(self):
        audit = STAUDITFILE()
        audit.AUD_TAMREG = 1000
        audit.AUD_AAAAMMDD = b'20260304'
        audit.AUD_HHMMDDSS = b'14300000'
        audit.AUD_MQ_HEADER = b'\x01' * 512
        audit.AUD_SEC_HEADER = b'\x02' * SECHDR_SIZE
        audit.AUD_SPBDOC = b'<xml>test</xml>'
        audit.AUD_TAMREG_PREV = 1000

        packed = audit.pack()
        restored = STAUDITFILE.unpack(packed)

        assert restored.AUD_TAMREG == 1000
        assert restored.AUD_AAAAMMDD == b'20260304'
        assert restored.AUD_HHMMDDSS == b'14300000'
        assert restored.AUD_MQ_HEADER == b'\x01' * 512
        assert restored.AUD_TAMREG_PREV == 1000

    def test_spbdoc_truncated_at_32767(self):
        audit = STAUDITFILE()
        audit.AUD_SPBDOC = b'X' * 40000  # Over max
        packed = audit.pack()
        # Should be truncated to 32767
        restored = STAUDITFILE.unpack(packed)
        assert len(restored.AUD_SPBDOC) == 32767


class TestSTTASKSTATUS:
    """Tests for task status structure."""

    def test_pack_unpack_roundtrip(self):
        status = STTASKSTATUS(
            bTaskNum=3,
            bTaskName=b'BacenReq  ',
            iTaskAutomatic=1,
            iTaskIsRunning=1,
        )
        packed = status.pack()
        assert len(packed) == 16

        restored = STTASKSTATUS.unpack(packed)
        assert restored.bTaskNum == 3
        assert restored.bTaskName == b'BacenReq  '
        assert restored.iTaskAutomatic == 1
        assert restored.iTaskIsRunning == 1


class TestMIMSG:
    """Tests for the primary message structure (COMHDR + 8000 bytes)."""

    def test_default_data_is_8000_bytes(self):
        msg = MIMSG()
        assert len(msg.mdata) == MAXMSGLENGTH

    def test_pack_size(self):
        msg = MIMSG()
        packed = msg.pack()
        assert len(packed) == COMHDR_SIZE + MAXMSGLENGTH

    def test_pack_unpack_roundtrip(self):
        hdr = COMHDR(usMsgLength=COMHDR_SIZE + 10, ucFuncSgr=FUNC_POST, usDatLength=10)
        mdata = bytearray(MAXMSGLENGTH)
        mdata[:10] = b'HelloWorld'
        msg = MIMSG(hdr=hdr, mdata=mdata)

        packed = msg.pack()
        restored = MIMSG.unpack(packed)
        assert restored.hdr.usMsgLength == COMHDR_SIZE + 10
        assert restored.hdr.ucFuncSgr == FUNC_POST
        assert restored.mdata[:10] == bytearray(b'HelloWorld')

    def test_unpack_short_data_padded(self):
        """Data shorter than 8000 bytes should be zero-padded."""
        hdr = COMHDR(usMsgLength=COMHDR_SIZE + 5, usDatLength=5)
        short_data = hdr.pack() + b'Hello'
        restored = MIMSG.unpack(short_data)
        assert len(restored.mdata) == MAXMSGLENGTH
        assert restored.mdata[:5] == bytearray(b'Hello')
        assert restored.mdata[5:] == bytearray(MAXMSGLENGTH - 5)


class TestConstants:
    """Tests for module-level constants."""

    def test_maxmsglength(self):
        assert MAXMSGLENGTH == 8000

    def test_minmsglength(self):
        assert MINMSGLENGTH == 11

    def test_tasks_count(self):
        assert TASKS_COUNT == 9

    def test_func_values(self):
        assert FUNC_POST == 0x01
        assert FUNC_NOP == 0xFF
