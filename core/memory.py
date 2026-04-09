import sqlite3
import os
import json
from datetime import datetime

class MemoryManager:
    """Manages context memory (command history, preferences) via local SQLite DB."""

    def __init__(self):
        # Resolve config dir: ~/.jarvis/
        self.config_dir = os.path.expanduser("~/.jarvis")
        os.makedirs(self.config_dir, exist_ok=True)
        self.db_path = os.path.join(self.config_dir, "memory.db")
        
        self._init_db()

    def _get_connection(self):
        """Get an isolated sqlite3 connection per thread/call."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Command History Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_query TEXT,
                    executed_command TEXT,
                    success BOOLEAN,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Preferences & Aliases Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.commit()

    def record_command(self, original_query: str, executed_command: str, success: bool = True):
        """Record an executed command into the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO history (original_query, executed_command, success) VALUES (?, ?, ?)',
                (original_query, executed_command, success)
            )
            conn.commit()

    def get_recent_commands(self, limit: int = 5) -> list[dict]:
        """Fetch the most recent commands executed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT original_query, executed_command, timestamp, success FROM history ORDER BY id DESC LIMIT ?', 
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]  # Oldest to newest context

    def get_preference(self, key: str, default=None) -> str:
        """Fetch a specific user preference."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM preferences WHERE key = ?', (key,))
            row = cursor.fetchone()
            if row:
                return row['value']
            return default

    def set_preference(self, key: str, value: str):
        """Save a user preference."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)',
                (key, value)
            )
            conn.commit()

    def get_all_preferences(self) -> dict:
        """Get all preferences safely as a dictionary."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM preferences')
            return {row['key']: row['value'] for row in cursor.fetchall()}

