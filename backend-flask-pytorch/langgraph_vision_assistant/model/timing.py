"""Measure inference across all model attempts in one assistant request.

The service opens a timer; the model client adds each call's duration, including
replies that need correction. ContextVar keeps concurrent requests separate and
follows LangGraph's execution context. Loading and lock waiting are excluded.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from collections.abc import Iterator


@dataclass
class InferenceTiming:
    """Accumulated inference time for the current request."""

    milliseconds: float = 0


_current: ContextVar[InferenceTiming | None] = ContextVar('inference_timing', default=None)


@contextmanager
def measure_inference() -> Iterator[InferenceTiming]:
    """Start a request-local timer and release it when the workflow finishes."""
    timing = InferenceTiming()
    token = _current.set(timing)
    try:
        yield timing
    finally:
        _current.reset(token)


def record_inference(milliseconds: float) -> None:
    """Add one model attempt to the active request's timer, when present."""
    timing = _current.get()
    if timing is not None:
        timing.milliseconds += milliseconds
