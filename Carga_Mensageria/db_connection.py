"""
Database connection manager for Carga Mensageria.
Replaces Module1.bas global ADODB objects and the repetitive
IsNull/Trim pattern from the VB6 code.

Uses PostgreSQL via psycopg3.
"""

import psycopg
from psycopg.rows import dict_row
from config import DB_CONFIG


class DatabaseManager:
    """Manages PostgreSQL connections for the Carga Mensageria application."""

    def __init__(self, db_config: dict = None):
        """
        Initialize database manager.

        Args:
            db_config: Optional dict with PostgreSQL connection parameters.
                      If None, uses config.DB_CONFIG.
        """
        self.db_config = db_config or DB_CONFIG
        self._conn = None

    def connect(self):
        """Open connection to the PostgreSQL database."""
        self._conn = psycopg.connect(
            host=self.db_config["host"],
            port=self.db_config["port"],
            dbname=self.db_config["database"],
            user=self.db_config["user"],
            password=self.db_config["password"],
            row_factory=dict_row,
        )
        return self._conn

    def close(self):
        """Close the connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def connection(self):
        return self._conn

    def execute_query(self, sql: str) -> list:
        """Execute a SELECT query and return all rows as dicts."""
        cursor = self._conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def execute_scalar(self, sql: str):
        """Execute a query and return the first column of the first row."""
        cursor = self._conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        return row[list(row.keys())[0]] if row else None

    def execute_insert(self, table: str, data: dict):
        """Insert a single row into a table from a dict of column->value."""
        columns = ", ".join(f'"{col}"' for col in data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders})'
        cursor = self._conn.cursor()
        cursor.execute(sql, tuple(data.values()))

    def commit(self):
        """Commit the current transaction."""
        if self._conn:
            self._conn.commit()

    def rollback(self):
        """Rollback the current transaction."""
        if self._conn:
            self._conn.rollback()

    @staticmethod
    def safe_trim(value) -> str:
        """Safely convert a possibly-None DB value to a trimmed string.

        Replaces the repetitive VB6 pattern:
            If IsNull(DBRS1("field")) Then str = "" Else str = Trim(DBRS1("field"))
        """
        if value is None:
            return ""
        return str(value).strip()
