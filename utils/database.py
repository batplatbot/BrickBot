import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any


class Database:
    """SQLite database wrapper with async support."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None

    async def initialise(self):
        """Initialise database connection and create tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        await self._create_tables()

    async def _create_tables(self):
        """Create all required tables."""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                group_id INTEGER,
                warnings TEXT DEFAULT '[]',
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, group_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS group_config (
                group_id INTEGER PRIMARY KEY,
                config TEXT DEFAULT '{}'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                message TEXT,
                remind_at TEXT,
                executed BOOLEAN DEFAULT FALSE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS command_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT,
                user_id INTEGER,
                group_id INTEGER,
                used_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        cursor = self.connection.cursor()
        for sql in tables:
            cursor.execute(sql)
        self.connection.commit()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return cursor."""
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        self.connection.commit()
        return cursor

    async def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Async wrapper for execute."""
        return self.execute(sql, params)

    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row as a dict."""
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    async def fetch_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Async wrapper for fetch_one."""
        return self.fetch_one(sql, params)

    def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows as a list of dicts."""
        cursor = self.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    async def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Async wrapper for fetch_all."""
        return self.fetch_all(sql, params)

    async def close(self):
        if self.connection:
            self.connection.close()
