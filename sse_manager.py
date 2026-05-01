import queue
import threading


class SSEManager:
    def __init__(self):
        self._subscribers = []
        self._lock = threading.Lock()

    def subscribe(self):
        q = queue.Queue(maxsize=100)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q):
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def broadcast(self, event_type, data):
        with self._lock:
            dead = []
            for q in self._subscribers:
                try:
                    q.put_nowait({'event': event_type, 'data': data})
                except queue.Full:
                    dead.append(q)
            for q in dead:
                self._subscribers.remove(q)


sse_manager = SSEManager()
