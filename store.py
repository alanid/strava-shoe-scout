"""
Lightweight key-value store for pending shoe-choice requests.

Keys are phone numbers (E.164 format), values are dicts with:
  - activity_id: int
  - shoes: list[dict]
  - access_token: str

Uses a simple in-memory dict. Fine for a single-user app on Render free tier
(one dyno, one process). If you ever scale to multiple workers, swap this
out for Redis or a SQLite file on a persistent disk.
"""

import threading


class PendingActivityStore:
    def __init__(self):
        self._lock  = threading.Lock()
        self._store: dict[str, dict] = {}

    def set(self, phone: str, data: dict):
        with self._lock:
            self._store[phone] = data

    def get(self, phone: str) -> dict | None:
        with self._lock:
            return self._store.get(phone)

    def clear(self, phone: str):
        with self._lock:
            self._store.pop(phone, None)
