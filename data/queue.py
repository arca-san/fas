#!/usr/bin/env python3
"""
SQLite tabanlı persistent job queue + token bucket rate limiter.
TEFAS API rate limit aşımını önler ve başarısız istekleri otomatik yeniden dener.
"""

import os
import time
import json
import threading
from datetime import datetime

from config.settings import PROJECT_ROOT

QUEUE_DB = str(PROJECT_ROOT / "data" / "queue.db")


class RateLimiter:
    """Token bucket rate limiter. Dakikada max_requests istek izni verir."""

    def __init__(self, max_rpm=6):
        self.max_rpm = max_rpm
        self.tokens = max_rpm
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_rpm, self.tokens + elapsed * (self.max_rpm / 60.0))
        self.last_refill = now

    def acquire(self, block=True):
        """Bir token al. Bloklama modunda token gelene kadar bekle."""
        while True:
            with self.lock:
                self._refill()
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
            if block:
                time.sleep(0.5)
            else:
                return False


class JobQueue:
    """SQLite tabanlı persistent job queue.

    Tablo: jobs (id, task_name, params, status, retries, max_retries, error, created_at)
    Status: pending, running, completed, failed
    """

    def __init__(self, db_path=None):
        self.db_path = db_path or QUEUE_DB
        self._init_db()

    def _init_db(self):
        import sqlite3
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                params TEXT,
                status TEXT DEFAULT 'pending',
                retries INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                error TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()

    def enqueue(self, task_name: str, params: dict = None, max_retries: int = 3):
        """İşi kuyruğa ekle."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO jobs (task_name, params, max_retries) VALUES (?, ?, ?)",
            (task_name, json.dumps(params or {}), max_retries),
        )
        conn.commit()
        conn.close()

    def dequeue(self):
        """Sıradaki pending işi al, status'ü running yap."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "SELECT id, task_name, params FROM jobs WHERE status='pending' ORDER BY id LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            conn.execute("UPDATE jobs SET status='running' WHERE id=?", (row[0],))
            conn.commit()
            conn.close()
            return {"id": row[0], "task_name": row[1], "params": json.loads(row[2] or "{}")}
        conn.close()
        return None

    def complete(self, job_id: int):
        """İşi başarılı olarak işaretle."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE jobs SET status='completed' WHERE id=?", (job_id,))
        conn.commit()
        conn.close()

    def fail(self, job_id: int, error: str = ""):
        """İşi başarısız olarak işaretle. Retry hakkı varsa yeniden kuyruğa al."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT retries, max_retries FROM jobs WHERE id=?", (job_id,))
        row = cur.fetchone()
        if row and row[0] < row[1]:
            conn.execute(
                "UPDATE jobs SET status='pending', retries=retries+1, error=? WHERE id=?",
                (error, job_id),
            )
        else:
            conn.execute("UPDATE jobs SET status='failed', error=? WHERE id=?", (error, job_id))
        conn.commit()
        conn.close()

    def stats(self):
        """Kuyruk istatistikleri."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("""
            SELECT status, COUNT(*) FROM jobs GROUP BY status
        """)
        stats = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
        return stats
