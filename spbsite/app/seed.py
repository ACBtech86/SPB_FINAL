"""Seed script to create initial data.

Usage: python -m app.seed
"""

import asyncio

from passlib.hash import bcrypt
from sqlalchemy import select

from app.database import Base, async_session, engine
from spb_shared.models import User
from spb_shared.models import SPBDicionario, SPBMensagem, SPBMsgField


async def seed():
    """Create database tables and seed initial data."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Create admin user if not exists
        result = await db.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                password_hash=bcrypt.hash("admin"),
                is_active=True,
            )
            db.add(admin)
            print("Created admin user (username: admin, password: admin)")

        # Seed message types
        result = await db.execute(select(SPBMensagem).limit(1))
        if not result.scalar_one_or_none():
            sample_messages = [
                SPBMensagem(msg_id="STR0001", msg_descr="Requisicao de Transferencia de Fundos"),
                SPBMensagem(msg_id="STR0001R1", msg_descr="Resposta de Transferencia de Fundos"),
                SPBMensagem(msg_id="STR0002", msg_descr="Requisicao de Transferencia de Reservas"),
                SPBMensagem(msg_id="STR0002R1", msg_descr="Resposta de Transferencia de Reservas"),
                SPBMensagem(msg_id="STR0003", msg_descr="Requisicao de Consulta de Saldo"),
                SPBMensagem(msg_id="STR0003R1", msg_descr="Resposta de Consulta de Saldo"),
                SPBMensagem(msg_id="STR0004", msg_descr="Requisicao de Abertura do Sistema"),
                SPBMensagem(msg_id="STR0005", msg_descr="Requisicao de Fechamento do Sistema"),
                SPBMensagem(msg_id="RCO0001", msg_descr="Requisicao de Compra/Venda de Cambio"),
                SPBMensagem(msg_id="SEL0001", msg_descr="Requisicao SELIC - Operacao Compromissada"),
            ]
            db.add_all(sample_messages)
            print(f"Created {len(sample_messages)} sample message types")

        # Seed field dictionary (SPB_DICIONARIO)
        result = await db.execute(select(SPBDicionario).limit(1))
        if not result.scalar_one_or_none():
            dicionario = [
                # Common field types
                SPBDicionario(msg_cpotag="CodMsg", msg_cpotipo="alfanumerico", msg_cpotam="9", msg_cpoform=""),
                SPBDicionario(msg_cpotag="NumCtrlIF", msg_cpotipo="alfanumerico", msg_cpotam="20", msg_cpoform=""),
                SPBDicionario(msg_cpotag="ISPB", msg_cpotipo="alfanumerico", msg_cpotam="8", msg_cpoform=""),
                SPBDicionario(msg_cpotag="CNPJIF", msg_cpotipo="alfanumerico", msg_cpotam="14", msg_cpoform=""),
                SPBDicionario(msg_cpotag="CNPJIFDeb", msg_cpotipo="alfanumerico", msg_cpotam="14", msg_cpoform=""),
                SPBDicionario(msg_cpotag="CNPJIFCred", msg_cpotipo="alfanumerico", msg_cpotam="14", msg_cpoform=""),
                SPBDicionario(msg_cpotag="AgDeb", msg_cpotipo="alfanumerico", msg_cpotam="4", msg_cpoform=""),
                SPBDicionario(msg_cpotag="AgCred", msg_cpotipo="alfanumerico", msg_cpotam="4", msg_cpoform=""),
                SPBDicionario(msg_cpotag="VlrLanc", msg_cpotipo="numerico", msg_cpotam="15", msg_cpoform=""),
                SPBDicionario(msg_cpotag="DtMovto", msg_cpotipo="alfanumerico", msg_cpotam="10", msg_cpoform="data"),
                SPBDicionario(msg_cpotag="DtRef", msg_cpotipo="alfanumerico", msg_cpotam="10", msg_cpoform="data"),
                SPBDicionario(msg_cpotag="DtHrSTR", msg_cpotipo="alfanumerico", msg_cpotam="19", msg_cpoform="data hora"),
                SPBDicionario(msg_cpotag="NivelPref", msg_cpotipo="alfanumerico", msg_cpotam="1", msg_cpoform=""),
                SPBDicionario(msg_cpotag="Finldd", msg_cpotipo="alfanumerico", msg_cpotam="3", msg_cpoform=""),
                SPBDicionario(msg_cpotag="Historico", msg_cpotipo="alfanumerico", msg_cpotam="200", msg_cpoform=""),
                SPBDicionario(msg_cpotag="TipoPessoaRemet", msg_cpotipo="alfanumerico", msg_cpotam="1", msg_cpoform=""),
                SPBDicionario(msg_cpotag="CNPJ_CPFRemet", msg_cpotipo="alfanumerico", msg_cpotam="14", msg_cpoform=""),
                SPBDicionario(msg_cpotag="NomRemet", msg_cpotipo="alfanumerico", msg_cpotam="100", msg_cpoform=""),
                SPBDicionario(msg_cpotag="TipoPessoaDestinatario", msg_cpotipo="alfanumerico", msg_cpotam="1", msg_cpoform=""),
                SPBDicionario(msg_cpotag="CNPJ_CPFDestinatario", msg_cpotipo="alfanumerico", msg_cpotam="14", msg_cpoform=""),
                SPBDicionario(msg_cpotag="NomDestinatario", msg_cpotipo="alfanumerico", msg_cpotam="100", msg_cpoform=""),
                SPBDicionario(msg_cpotag="CodGrade", msg_cpotipo="alfanumerico", msg_cpotam="5", msg_cpoform=""),
                SPBDicionario(msg_cpotag="HrioAb", msg_cpotipo="alfanumerico", msg_cpotam="8", msg_cpoform="hora"),
                SPBDicionario(msg_cpotag="HrioFch", msg_cpotipo="alfanumerico", msg_cpotam="8", msg_cpoform="hora"),
                SPBDicionario(msg_cpotag="TipoHrio", msg_cpotipo="alfanumerico", msg_cpotam="1", msg_cpoform=""),
                SPBDicionario(msg_cpotag="CodRCO", msg_cpotipo="alfanumerico", msg_cpotam="5", msg_cpoform=""),
            ]
            db.add_all(dicionario)
            print(f"Created {len(dicionario)} dictionary entries")

        # Seed field definitions (SPB_MSGFIELD)
        result = await db.execute(select(SPBMsgField).limit(1))
        if not result.scalar_one_or_none():
            fields = _build_field_definitions()
            db.add_all(fields)
            print(f"Created {len(fields)} field definitions")

        await db.commit()
        print("Seed completed successfully.")


def _build_field_definitions() -> list[SPBMsgField]:
    """Build SPBMsgField entries for all message types."""
    fields = []

    # --- STR0001: Requisicao de Transferencia de Fundos ---
    fields.extend(_msg_fields("BCN01", "STR0001", "STR0001", "Transferencia de Fundos", [
        ("Grupo_STR0001_MsgBody", "Corpo da Mensagem", "N"),
        ("CodMsg", "Codigo da Mensagem", "S"),
        ("NumCtrlIF", "Numero Controle IF", "S"),
        ("CNPJIFDeb", "CNPJ IF Debitada", "S"),
        ("AgDeb", "Agencia Debito", "S"),
        ("CNPJIFCred", "CNPJ IF Creditada", "S"),
        ("AgCred", "Agencia Credito", "S"),
        ("VlrLanc", "Valor do Lancamento", "S"),
        ("NivelPref", "Nivel de Preferencia", "N"),
        ("DtMovto", "Data Movimento", "S"),
        ("/Grupo_STR0001_MsgBody", "", "N"),
    ]))

    # --- STR0001R1: Resposta de Transferencia de Fundos ---
    fields.extend(_msg_fields("BCN01", "STR0001R1", "STR0001R1", "Resposta Transferencia", [
        ("Grupo_STR0001R1_MsgBody", "Corpo da Resposta", "N"),
        ("CodMsg", "Codigo da Mensagem", "S"),
        ("NumCtrlIF", "Numero Controle IF", "S"),
        ("DtHrSTR", "Data/Hora STR", "S"),
        ("DtMovto", "Data Movimento", "S"),
        ("/Grupo_STR0001R1_MsgBody", "", "N"),
    ]))

    # --- STR0002: Requisicao de Transferencia de Reservas ---
    fields.extend(_msg_fields("BCN01", "STR0002", "STR0002", "Transferencia de Reservas", [
        ("Grupo_STR0002_MsgBody", "Corpo da Mensagem", "N"),
        ("CodMsg", "Codigo da Mensagem", "S"),
        ("NumCtrlIF", "Numero Controle IF", "S"),
        ("CNPJIFDeb", "CNPJ IF Debitada", "S"),
        ("CNPJIFCred", "CNPJ IF Creditada", "S"),
        ("Finldd", "Finalidade", "S"),
        ("VlrLanc", "Valor do Lancamento", "S"),
        ("Historico", "Historico", "S"),
        ("NivelPref", "Nivel de Preferencia", "N"),
        ("DtMovto", "Data Movimento", "S"),
        ("/Grupo_STR0002_MsgBody", "", "N"),
    ]))

    # --- STR0002R1: Resposta de Transferencia de Reservas ---
    fields.extend(_msg_fields("BCN01", "STR0002R1", "STR0002R1", "Resposta Transferencia Reservas", [
        ("Grupo_STR0002R1_MsgBody", "Corpo da Resposta", "N"),
        ("CodMsg", "Codigo da Mensagem", "S"),
        ("NumCtrlIF", "Numero Controle IF", "S"),
        ("DtHrSTR", "Data/Hora STR", "S"),
        ("DtMovto", "Data Movimento", "S"),
        ("/Grupo_STR0002R1_MsgBody", "", "N"),
    ]))

    # --- STR0003: Requisicao de Consulta de Saldo ---
    fields.extend(_msg_fields("BCN01", "STR0003", "STR0003", "Consulta de Saldo", [
        ("Grupo_STR0003_MsgBody", "Corpo da Mensagem", "N"),
        ("CodMsg", "Codigo da Mensagem", "S"),
        ("NumCtrlIF", "Numero Controle IF", "S"),
        ("CNPJIF", "CNPJ da IF", "S"),
        ("DtRef", "Data de Referencia", "S"),
        ("DtMovto", "Data Movimento", "S"),
        ("/Grupo_STR0003_MsgBody", "", "N"),
    ]))

    # --- STR0003R1: Resposta de Consulta de Saldo ---
    fields.extend(_msg_fields("BCN01", "STR0003R1", "STR0003R1", "Resposta Consulta Saldo", [
        ("Grupo_STR0003R1_MsgBody", "Corpo da Resposta", "N"),
        ("CodMsg", "Codigo da Mensagem", "S"),
        ("NumCtrlIF", "Numero Controle IF", "S"),
        ("CNPJIF", "CNPJ da IF", "S"),
        ("VlrLanc", "Saldo", "S"),
        ("DtHrSTR", "Data/Hora STR", "S"),
        ("DtMovto", "Data Movimento", "S"),
        ("/Grupo_STR0003R1_MsgBody", "", "N"),
    ]))

    # --- STR0004: Requisicao de Abertura do Sistema ---
    fields.extend(_msg_fields("BCN01", "STR0004", "STR0004", "Abertura do Sistema", [
        ("Grupo_STR0004_MsgBody", "Corpo da Mensagem", "N"),
        ("CodMsg", "Codigo da Mensagem", "S"),
        ("NumCtrlIF", "Numero Controle IF", "S"),
        ("ISPB", "ISPB da Instituicao", "S"),
        ("DtHrSTR", "Data/Hora STR", "S"),
        ("DtMovto", "Data Movimento", "S"),
        ("/Grupo_STR0004_MsgBody", "", "N"),
    ]))

    # --- STR0005: Requisicao de Fechamento do Sistema ---
    fields.extend(_msg_fields("BCN01", "STR0005", "STR0005", "Fechamento do Sistema", [
        ("Grupo_STR0005_MsgBody", "Corpo da Mensagem", "N"),
        ("CodMsg", "Codigo da Mensagem", "S"),
        ("NumCtrlIF", "Numero Controle IF", "S"),
        ("ISPB", "ISPB da Instituicao", "S"),
        ("DtHrSTR", "Data/Hora STR", "S"),
        ("DtMovto", "Data Movimento", "S"),
        ("/Grupo_STR0005_MsgBody", "", "N"),
    ]))

    # --- RCO0001: Requisicao de Compra/Venda de Cambio ---
    fields.extend(_msg_fields("BCN01", "RCO0001", "RCO0001", "Compra/Venda de Cambio", [
        ("Grupo_RCO0001_MsgBody", "Corpo da Mensagem", "N"),
        ("CodMsg", "Codigo da Mensagem", "S"),
        ("NumCtrlIF", "Numero Controle IF", "S"),
        ("CNPJIF", "CNPJ da IF", "S"),
        ("CodRCO", "Codigo RCO", "S"),
        ("DtRef", "Data de Referencia", "S"),
        ("DtMovto", "Data Movimento", "S"),
        ("/Grupo_RCO0001_MsgBody", "", "N"),
    ]))

    # --- SEL0001: Requisicao SELIC - Operacao Compromissada ---
    fields.extend(_msg_fields("SEL01", "SEL0001", "SEL0001", "Operacao Compromissada SELIC", [
        ("Grupo_SEL0001_MsgBody", "Corpo da Mensagem", "N"),
        ("CodMsg", "Codigo da Mensagem", "S"),
        ("NumCtrlIF", "Numero Controle IF", "S"),
        ("CNPJIF", "CNPJ da IF", "S"),
        ("VlrLanc", "Valor da Operacao", "S"),
        ("DtRef", "Data de Referencia", "S"),
        ("DtMovto", "Data Movimento", "S"),
        ("/Grupo_SEL0001_MsgBody", "", "N"),
    ]))

    return fields


def _msg_fields(
    cod_grade: str, msg_id: str, msg_tag: str, msg_descr: str,
    field_list: list[tuple[str, str, str]],
) -> list[SPBMsgField]:
    """Helper to create SPBMsgField entries for a message type."""
    return [
        SPBMsgField(
            cod_grade=cod_grade,
            msg_id=msg_id,
            msg_tag=msg_tag,
            msg_descr=msg_descr,
            msg_emissor="61377677",
            msg_destinatario="00038166" if cod_grade != "SEL01" else "00038121",
            msg_seq=seq,
            msg_cpotag=cpotag,
            msg_cponome=cponome,
            msg_cpoobrig=obrig,
        )
        for seq, (cpotag, cponome, obrig) in enumerate(field_list, start=1)
    ]


if __name__ == "__main__":
    asyncio.run(seed())
