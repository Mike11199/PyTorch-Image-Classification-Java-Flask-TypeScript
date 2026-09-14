"""Local job records with atomic version checks."""

import json
import sqlite3
from pathlib import Path


class SqliteRecords:
    """Store records in the existing jobs.sqlite database."""

    def __init__(self, root: Path):
        """Create the record table if this is the first local run."""
        self.path = root / "jobs.sqlite"
        with self.connection() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, body TEXT NOT NULL)"
            )

    def connection(self):
        """Open a short-lived database connection."""
        return sqlite3.connect(self.path, timeout=10)

    def get(self, key):
        with self.connection() as db:
            row = db.execute("SELECT body FROM records WHERE id=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, record, expected):
        """Write only when the stored version matches the caller's version."""
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT body FROM records WHERE id=?", (record["id"],)
            ).fetchone()
            version = json.loads(row[0])["version"] if row else None
            if version != expected:
                return None
            db.execute(
                "INSERT OR REPLACE INTO records VALUES (?, ?)",
                (record["id"], json.dumps(record)),
            )
        return record

    def all(self):
        """Read records for queue selection and local cleanup."""
        with self.connection() as db:
            return [
                json.loads(row[0]) for row in db.execute("SELECT body FROM records")
            ]

    def delete(self, key):
        """Delete an expired local record."""
        with self.connection() as db:
            db.execute("DELETE FROM records WHERE id=?", (key,))
