"""Tests for frame-budgeted main-thread callback processing."""

from unittest.mock import patch

from async_worker import AsyncWorker


def test_process_pending_respects_callback_limit():
    worker = AsyncWorker()
    calls = []
    for value in range(3):
        worker.post_ui(lambda value=value: calls.append(value))

    processed = worker.process_pending(time_budget_seconds=None, max_callbacks=2)

    assert processed == 2
    assert calls == [0, 1]
    assert worker.process_pending(time_budget_seconds=None, max_callbacks=None) == 1
    assert calls == [0, 1, 2]


def test_process_pending_yields_after_time_budget():
    worker = AsyncWorker()
    calls = []
    worker.post_ui(lambda: calls.append("first"))
    worker.post_ui(lambda: calls.append("second"))

    with patch("async_worker.time.perf_counter", side_effect=[10.0, 10.005]):
        processed = worker.process_pending(
            time_budget_seconds=0.004,
            max_callbacks=None,
        )

    assert processed == 1
    assert calls == ["first"]
    assert worker.process_pending(time_budget_seconds=None, max_callbacks=None) == 1
    assert calls == ["first", "second"]


def test_background_result_is_delivered_through_ui_queue():
    worker = AsyncWorker()
    results = []

    thread = worker.run_async(task=lambda: 42, on_done=results.append)
    thread.join(timeout=1)

    assert results == []
    assert worker.process_pending(time_budget_seconds=None, max_callbacks=None) == 1
    assert results == [42]
