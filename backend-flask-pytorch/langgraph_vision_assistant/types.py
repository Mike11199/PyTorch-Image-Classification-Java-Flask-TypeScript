"""Describe replies shared by the HTTP endpoint and assistant workflow.

AssistantResult carries browser commands, clarification text, and timings.
Viewer input and validated state live in viewer/state.py; browser command
shapes live in viewer/commands.py. These types do not depend on LangGraph.
"""

from typing_extensions import NotRequired, TypedDict
from .viewer.commands import ViewerCommand


class AssistantTiming(TypedDict):
    """Measured server durations; inference excludes loading and waiting."""

    inference_ms: int
    total_ms: int


class AssistantResult(TypedDict):
    """Existing frontend response: commands to apply, or a clarification."""

    actions: list[ViewerCommand]
    message: str
    timing: NotRequired[AssistantTiming]


class ErrorResponse(TypedDict):
    """User-facing HTTP failure, without backend exception details."""

    error: str
