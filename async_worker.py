"""Thread-safe async worker for running background tasks in DearPyGUI applications.

DearPyGUI is not thread-safe — all UI calls must happen on the main thread.
Use AsyncWorker to offload blocking operations (DB queries, network calls) to
background threads, then post UI update callbacks into the queue.

The main render loop must call process_pending() every frame to drain the queue.
"""

import queue
import threading
from typing import Any, Callable


class AsyncWorker:
    """Runs tasks on daemon threads and delivers results to the main thread via a queue.

    Usage:
        worker = AsyncWorker()

        # In each frame of the render loop:
        worker.process_pending()

        # To run a blocking task without freezing the UI:
        worker.run_async(
            task=lambda: db.execute_query(sql),
            on_done=lambda result: build_table_ui(result),
            on_error=lambda e: show_error(str(e)),
        )
    """

    def __init__(self):
        self._ui_queue: queue.SimpleQueue = queue.SimpleQueue()
        self._active = 0
        self._lock = threading.Lock()

    @property
    def is_busy(self) -> bool:
        """True if any background task is currently running."""
        with self._lock:
            return self._active > 0

    def run_async(
        self,
        task: Callable[[], Any],
        on_done: Callable[[Any], None] = None,
        on_error: Callable[[Exception], None] = None,
    ) -> threading.Thread:
        """Submit a task to run on a daemon background thread.

        on_done(result) and on_error(exception) are enqueued and will be
        called on the main thread during the next process_pending() call.

        Args:
            task: Callable that runs on the background thread (no UI calls allowed).
            on_done: Called on main thread with the task's return value.
            on_error: Called on main thread with the exception if task raises.

        Returns:
            The started background Thread.
        """
        with self._lock:
            self._active += 1

        def _worker():
            try:
                result = task()
                if on_done is not None:
                    self._ui_queue.put(lambda r=result: on_done(r))
            except Exception as exc:
                if on_error is not None:
                    self._ui_queue.put(lambda e=exc: on_error(e))
            finally:
                with self._lock:
                    self._active -= 1

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    def process_pending(self):
        """Drain all pending UI callbacks. Must be called from the main thread each frame."""
        while True:
            try:
                fn = self._ui_queue.get_nowait()
                fn()
            except queue.Empty:
                break
