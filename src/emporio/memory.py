"""Conversation history, kept in SQLite next to the store data.

Only the dialogue is stored. Tool results are deliberately left out: they are a
snapshot of stock and prices at the time of the answer, and replaying a stale
one later is exactly the mistake the policy manual warns about.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
"""


class History:
    def __init__(self, session_id: str, db_path: Path | None = None,
                 max_turns: int = config.HISTORY_TURNS):
        self.session_id = session_id
        self.max_turns = max_turns
        self._db_path = db_path or config.DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def append(self, role: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO messages (session_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (self.session_id, role, content, datetime.now().isoformat(timespec="seconds")),
            )

    def messages(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT role, content FROM messages WHERE session_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (self.session_id, self.max_turns * 2),
            ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM messages WHERE session_id = ?", (self.session_id,))
