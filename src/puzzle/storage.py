"""Local profiles and completed attempts, using the standard-library SQLite API."""

from pathlib import Path
import sqlite3
from datetime import datetime, timezone


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=2)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                name_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
                last_seen TEXT NOT NULL, visits INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY, title TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('builtin', 'upload'))
            );
            CREATE TABLE IF NOT EXISTS attempts (
                id TEXT PRIMARY KEY,
                player_id INTEGER NOT NULL REFERENCES players(id),
                image_id TEXT NOT NULL REFERENCES images(id),
                grid_size INTEGER NOT NULL CHECK(grid_size BETWEEN 2 AND 32),
                elapsed_ms INTEGER NOT NULL CHECK(elapsed_ms >= 0),
                moves INTEGER NOT NULL CHECK(moves >= 0),
                completed_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS attempt_ranking
            ON attempts(image_id, grid_size, elapsed_ms, moves);
        """)

    def close(self) -> None:
        self.db.close()

    def select_player(self, name: str) -> sqlite3.Row:
        name = " ".join(name.split())
        if not name or len(name) > 24 or not name.isprintable():
            raise ValueError("Use a name with 1 to 24 visible characters.")
        now = timestamp()
        with self.db:
            self.db.execute("""
                INSERT INTO players(name, name_key, created_at, last_seen)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name_key) DO UPDATE
                SET last_seen = excluded.last_seen, visits = players.visits + 1
            """, (name, name.casefold(), now, now))
        return self.db.execute("SELECT * FROM players WHERE name_key = ?",
                               (name.casefold(),)).fetchone()

    def players(self) -> list[sqlite3.Row]:
        return self.db.execute("""
            SELECT p.*, COUNT(a.id) AS solved FROM players p
            LEFT JOIN attempts a ON a.player_id = p.id
            GROUP BY p.id ORDER BY p.last_seen DESC, p.id DESC
        """).fetchall()

    def register_image(self, image_id: str, title: str, kind: str) -> None:
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO images VALUES (?, ?, ?)",
                            (image_id, title, kind))

    def images(self) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM images ORDER BY kind, title, id").fetchall()

    def save_result(self, attempt_id: str, player_id: int, image_id: str,
                    size: int, elapsed_seconds: float, moves: int) -> None:
        with self.db:
            self.db.execute("""
                INSERT INTO attempts VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO NOTHING
            """, (attempt_id, player_id, image_id, size,
                  round(elapsed_seconds * 1000), moves, timestamp()))

    def leaderboard(self, image_id: str, size: int) -> list[sqlite3.Row]:
        return self.db.execute("""
            SELECT a.*, p.name,
                   RANK() OVER (ORDER BY a.elapsed_ms, a.moves) AS rank
            FROM attempts a JOIN players p ON p.id = a.player_id
            WHERE a.image_id = ? AND a.grid_size = ?
            ORDER BY a.elapsed_ms, a.moves, a.completed_at, a.id LIMIT 100
        """, (image_id, size)).fetchall()

    def personal_best(self, player_id: int, image_id: str, size: int):
        return self.db.execute("""
            SELECT * FROM attempts WHERE player_id = ? AND image_id = ? AND grid_size = ?
            ORDER BY elapsed_ms, moves, completed_at, id LIMIT 1
        """, (player_id, image_id, size)).fetchone()

    def rank(self, attempt_id: str) -> int:
        return self.db.execute("""
            SELECT 1 + COUNT(*) FROM attempts a JOIN attempts current
            ON current.id = ? AND a.image_id = current.image_id
            AND a.grid_size = current.grid_size
            WHERE (a.elapsed_ms, a.moves) < (current.elapsed_ms, current.moves)
        """, (attempt_id,)).fetchone()[0]
