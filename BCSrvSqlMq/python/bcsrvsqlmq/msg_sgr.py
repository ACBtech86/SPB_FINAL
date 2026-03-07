# msg_sgr.py - Message structures (port of MsgSgr.h)

import struct
from dataclasses import dataclass, field

MAXMSGLENGTH = 8000
MINMSGLENGTH = 11  # sizeof(COMHDR)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

FILE_CLOSE = 0x00
FILE_OPEN = 0x01

Resposta_OK = 0

# Task identifiers
TASKS_MONITOR = 0x00
TASKS_BACENREQ = 0x01
TASKS_BACENRSP = 0x02
TASKS_BACENREP = 0x03
TASKS_BACENSUP = 0x04
TASKS_IFREQ = 0x05
TASKS_IFRSP = 0x06
TASKS_IFREP = 0x07
TASKS_IFSUP = 0x08
TASKS_COUNT = 9

# STR functions
FUNC_POST = 0x01
FUNC_NOP = 0xFF

# --------------------------------------------------------------------------
# COMHDR - TCP/IP communication header (11 bytes, packed)
# --------------------------------------------------------------------------
# Layout: usMsgLength(2) + ucIdHeader(4) + ucFuncSgr(1) + usRc(2) + usDatLength(2)
COMHDR_FORMAT = '<H4sBHH'
COMHDR_SIZE = struct.calcsize(COMHDR_FORMAT)  # 11 bytes


@dataclass
class COMHDR:
    usMsgLength: int = 0          # Message size
    ucIdHeader: bytes = field(default_factory=lambda: b'\x00' * 4)  # Header ID
    ucFuncSgr: int = 0            # Function
    usRc: int = 0                 # Return Code
    usDatLength: int = 0          # Data size

    def pack(self) -> bytes:
        return struct.pack(
            COMHDR_FORMAT,
            self.usMsgLength,
            self.ucIdHeader[:4],
            self.ucFuncSgr,
            self.usRc,
            self.usDatLength,
        )

    @classmethod
    def unpack(cls, data: bytes) -> 'COMHDR':
        values = struct.unpack(COMHDR_FORMAT, data[:COMHDR_SIZE])
        return cls(
            usMsgLength=values[0],
            ucIdHeader=values[1],
            ucFuncSgr=values[2],
            usRc=values[3],
            usDatLength=values[4],
        )


# --------------------------------------------------------------------------
# SECHDR - Security header V2 (588 bytes, packed)
# --------------------------------------------------------------------------
# Layout per Manual de Segurança do SFN v5 (BACEN 2024 update):
#   C01 TamSecHeader(2)        pos 001-002  Fixed 0x024C (588)
#   C02 Versao(1)              pos 003      00h=clear, 02h=V2
#   C03 CodErro(1)             pos 004      Error code
#   C04 TratamentoEspecial(1)  pos 005      Special treatment indicator
#   C05 Reservado(1)           pos 006      Reserved 00h
#   C06 AlgAssymKey(1)         pos 007      01h=RSA-1024, 02h=RSA-2048
#   C07 AlgSymKey(1)           pos 008      01h=3DES-168
#   C08 AlgAssymKeyLocal(1)    pos 009      01h=RSA-1024, 02h=RSA-2048
#   C09 AlgHash(1)             pos 010      02h=SHA-1, 03h=SHA-256
#   C10 CADest(1)              pos 011      CA identifier (01-05)
#   C11 NumSerieCertDest(32)   pos 012-043  Destination cert serial
#   C12 CALocal(1)             pos 044      CA identifier (01-05)
#   C13 NumSerieCertLocal(32)  pos 045-076  Local cert serial
#   C14 SymKeyCifr(256)        pos 077-332  RSA-wrapped symmetric key
#   C15 HashCifrSign(256)      pos 333-588  Digital signature
#   Total = 2+1+1+1+1+1+1+1+1+1+32+1+32+256+256 = 588
SECHDR_FORMAT = '<2sBBBBBBBBB32sB32s256s256s'
SECHDR_SIZE = struct.calcsize(SECHDR_FORMAT)  # 588 bytes

# --- V1 legacy header (332 bytes) for backward compatibility ---
SECHDR_V1_FORMAT = '<2sBB2sBBBBB32sB32sB127sB127s'
SECHDR_V1_SIZE = struct.calcsize(SECHDR_V1_FORMAT)  # 332 bytes

# Algorithm constants
ALG_RSA_1024 = 0x01
ALG_RSA_2048 = 0x02
ALG_3DES_168 = 0x01
ALG_HASH_MD5 = 0x01       # V1 only (deprecated)
ALG_HASH_SHA1 = 0x02
ALG_HASH_SHA256 = 0x03

# Protocol version constants
SECHDR_VERSION_CLEAR = 0x00
SECHDR_VERSION_V1 = 0x01   # Legacy 332-byte header, RSA-1024
SECHDR_VERSION_V2 = 0x02   # New 588-byte header, RSA-2048

# CA constants
CA_SERPRO = 0x01
CA_CERTSIGN = 0x02
CA_SERASA = 0x03
CA_CAIXA = 0x04
CA_VALID = 0x05


@dataclass
class SECHDR:
    """Security header V2 (588 bytes) per Manual de Segurança do SFN v5."""
    TamSecHeader: bytes = field(default_factory=lambda: b'\x02\x4C')  # 588
    Versao: int = SECHDR_VERSION_V2       # 00h=clear, 02h=V2
    CodErro: int = 0
    TratamentoEspecial: int = 0           # C04: special treatment indicator
    Reservado: int = 0                    # C05: reserved 00h
    AlgAssymKey: int = ALG_RSA_2048       # C06: 02h=RSA-2048
    AlgSymKey: int = ALG_3DES_168         # C07: 01h=3DES-168
    AlgAssymKeyLocal: int = ALG_RSA_2048  # C08: 02h=RSA-2048
    AlgHash: int = ALG_HASH_SHA256        # C09: 03h=SHA-256
    CADest: int = 0                       # C10: CA identifier
    NumSerieCertDest: bytes = field(default_factory=lambda: b'\x00' * 32)
    CALocal: int = 0                      # C12: CA identifier
    NumSerieCertLocal: bytes = field(default_factory=lambda: b'\x00' * 32)
    SymKeyCifr: bytes = field(default_factory=lambda: b'\x00' * 256)   # C14: RSA-wrapped key
    HashCifrSign: bytes = field(default_factory=lambda: b'\x00' * 256) # C15: signature

    def pack(self) -> bytes:
        return struct.pack(
            SECHDR_FORMAT,
            self.TamSecHeader[:2],
            self.Versao,
            self.CodErro,
            self.TratamentoEspecial,
            self.Reservado,
            self.AlgAssymKey,
            self.AlgSymKey,
            self.AlgAssymKeyLocal,
            self.AlgHash,
            self.CADest,
            self.NumSerieCertDest[:32],
            self.CALocal,
            self.NumSerieCertLocal[:32],
            self.SymKeyCifr[:256],
            self.HashCifrSign[:256],
        )

    @classmethod
    def unpack(cls, data: bytes) -> 'SECHDR':
        # Auto-detect header version from size field (first 2 bytes)
        if len(data) >= 2:
            tam = int.from_bytes(data[0:2], 'little')
            if tam == SECHDR_V1_SIZE:
                return cls._unpack_v1(data)
        values = struct.unpack(SECHDR_FORMAT, data[:SECHDR_SIZE])
        return cls(
            TamSecHeader=values[0],
            Versao=values[1],
            CodErro=values[2],
            TratamentoEspecial=values[3],
            Reservado=values[4],
            AlgAssymKey=values[5],
            AlgSymKey=values[6],
            AlgAssymKeyLocal=values[7],
            AlgHash=values[8],
            CADest=values[9],
            NumSerieCertDest=values[10],
            CALocal=values[11],
            NumSerieCertLocal=values[12],
            SymKeyCifr=values[13],
            HashCifrSign=values[14],
        )

    @classmethod
    def _unpack_v1(cls, data: bytes) -> 'SECHDR':
        """Unpack legacy V1 332-byte header and promote to V2 layout."""
        values = struct.unpack(SECHDR_V1_FORMAT, data[:SECHDR_V1_SIZE])
        # V1 layout: IniSymKeyCifr(1B) + SymKeyCifr(127B) = 128 contiguous bytes
        ini_sym = bytes([values[12]])
        sym_key = values[13]
        sym_key_full = (ini_sym + sym_key).ljust(256, b'\x00')
        # V1 layout: IniHashCifrSign(1B) + HashCifrSign(127B) = 128 contiguous bytes
        ini_hash = bytes([values[14]])
        hash_sign = values[15]
        hash_sign_full = (ini_hash + hash_sign).ljust(256, b'\x00')
        # V1 Reservado was 2 bytes; split into TratamentoEspecial + Reservado
        reservado_v1 = values[3]
        return cls(
            TamSecHeader=values[0],
            Versao=values[1],
            CodErro=values[2],
            TratamentoEspecial=reservado_v1[0] if isinstance(reservado_v1, (bytes, bytearray)) else 0,
            Reservado=reservado_v1[1] if isinstance(reservado_v1, (bytes, bytearray)) else 0,
            AlgAssymKey=values[4],
            AlgSymKey=values[5],
            AlgAssymKeyLocal=values[6],
            AlgHash=values[7],
            CADest=values[8],
            NumSerieCertDest=values[9],
            CALocal=values[10],
            NumSerieCertLocal=values[11],
            SymKeyCifr=sym_key_full,
            HashCifrSign=hash_sign_full,
        )


# --------------------------------------------------------------------------
# STAUDITFILE - Audit file record structure
# --------------------------------------------------------------------------

@dataclass
class STAUDITFILE:
    AUD_TAMREG: int = 0                 # Record size
    AUD_AAAAMMDD: bytes = field(default_factory=lambda: b'\x00' * 8)
    AUD_HHMMDDSS: bytes = field(default_factory=lambda: b'\x00' * 8)
    AUD_MQ_HEADER: bytes = field(default_factory=lambda: b'\x00' * 512)
    AUD_SEC_HEADER: bytes = field(default_factory=lambda: b'\x00' * SECHDR_SIZE)
    AUD_SPBDOC: bytes = b''             # Variable length, up to 32767
    AUD_TAMREG_PREV: int = 0            # Previous record size

    def pack(self) -> bytes:
        spb_padded = self.AUD_SPBDOC[:32767].ljust(32767, b'\x00')
        data = struct.pack('<H', self.AUD_TAMREG)
        data += self.AUD_AAAAMMDD[:8].ljust(8, b'\x00')
        data += self.AUD_HHMMDDSS[:8].ljust(8, b'\x00')
        data += self.AUD_MQ_HEADER[:512].ljust(512, b'\x00')
        data += self.AUD_SEC_HEADER[:SECHDR_SIZE].ljust(SECHDR_SIZE, b'\x00')
        data += spb_padded
        data += struct.pack('<H', self.AUD_TAMREG_PREV)
        return data

    @classmethod
    def unpack(cls, data: bytes) -> 'STAUDITFILE':
        offset = 0
        aud_tamreg = struct.unpack_from('<H', data, offset)[0]
        offset += 2
        aud_date = data[offset:offset + 8]
        offset += 8
        aud_time = data[offset:offset + 8]
        offset += 8
        aud_mq = data[offset:offset + 512]
        offset += 512
        aud_sec = data[offset:offset + SECHDR_SIZE]
        offset += SECHDR_SIZE
        aud_spb = data[offset:offset + 32767]
        offset += 32767
        aud_tamreg_prev = struct.unpack_from('<H', data, offset)[0]
        return cls(
            AUD_TAMREG=aud_tamreg,
            AUD_AAAAMMDD=aud_date,
            AUD_HHMMDDSS=aud_time,
            AUD_MQ_HEADER=aud_mq,
            AUD_SEC_HEADER=aud_sec,
            AUD_SPBDOC=aud_spb,
            AUD_TAMREG_PREV=aud_tamreg_prev,
        )


# --------------------------------------------------------------------------
# STTASKSTATUS - Task status structure
# --------------------------------------------------------------------------

@dataclass
class STTASKSTATUS:
    bTaskNum: int = 0
    bTaskName: bytes = field(default_factory=lambda: b' ' * 10)
    iTaskAutomatic: int = 0
    iTaskIsRunning: int = 0

    def pack(self) -> bytes:
        return struct.pack('<i10sBB',
                           self.bTaskNum,
                           self.bTaskName[:10],
                           self.iTaskAutomatic,
                           self.iTaskIsRunning)

    @classmethod
    def unpack(cls, data: bytes) -> 'STTASKSTATUS':
        values = struct.unpack('<i10sBB', data[:16])
        return cls(
            bTaskNum=values[0],
            bTaskName=values[1],
            iTaskAutomatic=values[2],
            iTaskIsRunning=values[3],
        )


# --------------------------------------------------------------------------
# MIMSG - Primary message structure (COMHDR + 8000 bytes data)
# --------------------------------------------------------------------------

@dataclass
class MIMSG:
    hdr: COMHDR = field(default_factory=COMHDR)
    mdata: bytearray = field(default_factory=lambda: bytearray(MAXMSGLENGTH))

    def pack(self) -> bytes:
        return self.hdr.pack() + bytes(self.mdata[:MAXMSGLENGTH])

    @classmethod
    def unpack(cls, data: bytes) -> 'MIMSG':
        hdr = COMHDR.unpack(data[:COMHDR_SIZE])
        mdata = bytearray(data[COMHDR_SIZE:COMHDR_SIZE + MAXMSGLENGTH])
        if len(mdata) < MAXMSGLENGTH:
            mdata.extend(b'\x00' * (MAXMSGLENGTH - len(mdata)))
        return cls(hdr=hdr, mdata=mdata)
