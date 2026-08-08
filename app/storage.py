from threading import Lock


class MemoStore:
    def __init__(self, max_items=50, max_length=500):
        self.max_items = max_items
        self.max_length = max_length
        self._items = []
        self._lock = Lock()

    def add(self, value):
        if len(value) > self.max_length:
            return False
        with self._lock:
            self._items.append(value)
            if len(self._items) > self.max_items:
                del self._items[: len(self._items) - self.max_items]
        return True

    def list(self):
        with self._lock:
            return list(reversed(self._items))

    def clear(self):
        with self._lock:
            self._items.clear()
