"""
Database connection manager for Carga Mensageria.
Replaces Module1.bas global ADODB objects and the repetitive
IsNull/Trim pattern from the VB6 code.

Uses SQLite3 (built-in Python module) instead of SQL Server.
"""

import sqlite3


def _dict_factory(cursor, row):
    """Row factory that returns each row as a dict keyed by column name."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


class DatabaseManager:
    """Manages SQLite connections for the Carga Mensageria application."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    def connect(self):
        """Open connection to the SQLite database file."""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = _dict_factory
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
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
        # Use a plain row_factory for this single call
        cursor = self._conn.cursor()
        old_factory = self._conn.row_factory
        self._conn.row_factory = None
        plain_cursor = self._conn.cursor()
        plain_cursor.execute(sql)
        row = plain_cursor.fetchone()
        self._conn.row_factory = old_factory
        return row[0] if row else None

    def execute_insert(self, table: str, data: dict):
        """Insert a single row into a table from a dict of column->value."""
        columns = ", ".join(f"[{col}]" for col in data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO [{table}] ({columns}) VALUES ({placeholders})"
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
