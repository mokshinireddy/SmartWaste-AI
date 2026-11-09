
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "smartwaste.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 20000")
    return conn

def init_database():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS bins (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            capacity_kg REAL NOT NULL,
            fill_percent REAL NOT NULL,
            weight_kg REAL NOT NULL,
            daily_growth REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bin_id INTEGER NOT NULL,
            fill_percent REAL NOT NULL,
            weight_kg REAL NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bin_id) REFERENCES bins(id)
        );

        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bin_id INTEGER NOT NULL,
            previous_fill REAL NOT NULL,
            collected_weight_kg REAL NOT NULL,
            collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bin_id) REFERENCES bins(id)
        );

        CREATE TABLE IF NOT EXISTS simulation_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            last_tick TEXT NOT NULL
        );
        """)

        conn.execute("""
            INSERT OR IGNORE INTO simulation_state(id, last_tick)
            VALUES (1, CURRENT_TIMESTAMP)
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM bins"
        ).fetchone()[0]

        if count == 0:
            for i in range(1, 31):
                capacity = [50, 75, 100, 150, 200][i % 5]
                fill = 15 + (i * 17) % 80
                conn.execute("""
                    INSERT INTO bins VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    i, f"SW-{i:03d}",
                    f"Industrial Zone {(i - 1) // 5 + 1}",
                    capacity,
                    fill,
                    round(capacity * fill / 100, 2),
                    4 + i % 12
                ))

        conn.execute("""
            UPDATE bins
            SET name = printf('SW-%03d', id)
        """)
