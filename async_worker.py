"""Thread-safe async worker for running background tasks in DearPyGUI applications.

DearPyGUI is not thread-safe — all UI calls must happen on the main thread.
Use AsyncWorker to offload blocking operations (DB queries, network calls) to
background threads, then post UI update callbacks into the queue.

The main render loop must call process_pending() every frame to drain the queue.
"""

import queue
import threading
import time
from collections.abc import Callable
from typing import Any


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
                    self.post_ui(lambda r=result: on_done(r))
            except Exception as exc:
                if on_error is not None:
                    self.post_ui(lambda e=exc: on_error(e))
            finally:
                with self._lock:
                    self._active -= 1

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    def post_ui(self, callback: Callable[[], Any]) -> None:
        """Schedule a callback for the next available main-thread frame budget."""
        self._ui_queue.put(callback)

    def process_pending(
        self,
        *,
        time_budget_seconds: float | None = 0.004,
        max_callbacks: int | None = 8,
    ) -> int:
        """Run queued UI callbacks without monopolizing the current render frame.

        A callback is never interrupted. The limits are checked between callbacks,
        so one expensive callback can exceed the target budget but the remaining
        queue will be left for a later frame.
        """
        started_at = time.perf_counter()
        processed = 0

        while max_callbacks is None or processed < max_callbacks:
            try:
                fn = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            fn()
            processed += 1

            if (
                time_budget_seconds is not None
                and time.perf_counter() - started_at >= time_budget_seconds
            ):
                break

        return processed
