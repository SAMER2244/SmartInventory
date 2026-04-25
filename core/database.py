"""
Database Management Module.
Provides the context manager for SQLite transactions and initialization functions.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

class DatabaseManager:
    """Context manager for SQLite database transactions."""
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection = None

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.close()

def init_db(db_path: Path):
    """Initializes the database schema with expanded fields."""
    with DatabaseManager(db_path) as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stok (
                part_no TEXT PRIMARY KEY,
                quantity REAL DEFAULT 0,
                comment TEXT,
                designator TEXT,
                footprint TEXT,
                value TEXT,
                category TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Index for faster searching
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_part_no ON stok(part_no)")

def get_db_headers(db_path: Path) -> list:
    """Returns a list of column names from the 'stok' table using PRAGMA table_info."""
    if not db_path.exists():
        return []
    with DatabaseManager(db_path) as cursor:
        cursor.execute("PRAGMA table_info(stok)")
        return [row[1] for row in cursor.fetchall()]
