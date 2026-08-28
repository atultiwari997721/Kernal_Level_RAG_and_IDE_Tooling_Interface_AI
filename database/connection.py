"""Database Connection Manager for SQLite."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import threading
from typing import Generator, Optional

from config.settings import get_config
from database.schema import SCHEMA_SQL


class DatabaseConnection:
    """Thread-safe SQLite connection manager."""

    def __init__(self, db_path: Optional[Path] = None):
        self.config = get_config()
        self.db_path = db_path or self.config.db_path
        self._local = threading.local()
        self._init_db()

    def _init_db(self) -> None:
        """Ensure parent directory exists and execute schema DDL."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def _create_connection(self) -> sqlite3.Connection:
        """Create a configured SQLite connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a transactional connection context."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = self._create_connection()
            self._local.conn = conn
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()

    def close(self) -> None:
        """Close thread connection if open."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None
