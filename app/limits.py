from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class SubmissionLimiter:
    def __init__(self, limit, window_seconds, clock=monotonic):
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._events = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key):
        now = self._clock()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True
