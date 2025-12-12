"""Thread-safe query executor for ClickHouse Client.

This module provides a thread-safe way to execute database queries without blocking the UI.
"""

import threading
import time
from queue import Queue
from typing import Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum


class QueryStatus(Enum):
    """Status of a query execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueryResult:
    """Result of a query execution."""
    status: QueryStatus
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


class QueryExecutor:
    """Executes database queries in a background thread to keep UI responsive."""

    def __init__(self):
        """Initialize the query executor."""
        self.result_queue = Queue()
        self.current_thread: Optional[threading.Thread] = None
        self.cancel_flag = threading.Event()
        self._lock = threading.Lock()

    def execute_async(
        self,
        query_func: Callable,
        on_complete: Callable[[QueryResult], None],
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """
        Execute a query function asynchronously.

        Args:
            query_func: Function that executes the query (should return query result)
            on_complete: Callback function called when query completes (receives QueryResult)
            on_progress: Optional callback for progress updates (receives status message)

        Returns:
            bool: True if query was started, False if another query is already running
        """
        with self._lock:
            # Check if a query is already running
            if self.current_thread and self.current_thread.is_alive():
                return False

            # Reset cancel flag
            self.cancel_flag.clear()

            # Start query in background thread
            self.current_thread = threading.Thread(
                target=self._execute_query_thread,
                args=(query_func, on_complete, on_progress),
                daemon=True,
            )
            self.current_thread.start()
            return True

    def _execute_query_thread(
        self,
        query_func: Callable,
        on_complete: Callable[[QueryResult], None],
        on_progress: Optional[Callable[[str], None]] = None,
    ):
        """
        Internal method that runs in the background thread.

        Args:
            query_func: Function that executes the query
            on_complete: Callback function called when query completes
            on_progress: Optional callback for progress updates
        """
        start_time = time.time()
        result = QueryResult(status=QueryStatus.RUNNING)

        try:
            # Notify progress
            if on_progress:
                on_progress("Executing query...")

            # Check if cancelled before starting
            if self.cancel_flag.is_set():
                result.status = QueryStatus.CANCELLED
                on_complete(result)
                return

            # Execute the query function
            query_result = query_func()

            # Check if cancelled after execution
            if self.cancel_flag.is_set():
                result.status = QueryStatus.CANCELLED
                on_complete(result)
                return

            # Query completed successfully
            result.status = QueryStatus.COMPLETED
            result.result = query_result
            result.execution_time = time.time() - start_time

            # Notify progress
            if on_progress:
                on_progress(f"Query completed in {result.execution_time:.2f}s")

        except Exception as e:
            # Query failed
            result.status = QueryStatus.FAILED
            result.error = str(e)
            result.execution_time = time.time() - start_time

            # Notify progress
            if on_progress:
                on_progress(f"Query failed: {str(e)}")

        finally:
            # Call completion callback
            on_complete(result)

    def cancel_current_query(self) -> bool:
        """
        Cancel the currently running query.

        Returns:
            bool: True if a query was cancelled, False if no query was running
        """
        with self._lock:
            if self.current_thread and self.current_thread.is_alive():
                self.cancel_flag.set()
                return True
            return False

    def is_query_running(self) -> bool:
        """
        Check if a query is currently running.

        Returns:
            bool: True if a query is running, False otherwise
        """
        with self._lock:
            return self.current_thread is not None and self.current_thread.is_alive()
