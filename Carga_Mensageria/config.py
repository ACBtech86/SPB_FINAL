"""
Database configuration for PostgreSQL connection.

Set these values or use environment variables:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import os

# PostgreSQL connection settings
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "spb_mensageria"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# Default ISPB for Banco Cidade
BANCO_CIDADE_ISPB = "61377677"

# Output directories
HTML_OUTPUT_DIR = os.getenv("HTML_OUTPUT_DIR", r"C:\BCFONTES\SPB\Carga_Mensageria\HTML")
ISPB_OUTPUT_DIR = os.getenv("ISPB_OUTPUT_DIR", r"C:\LIXO\HTML")
