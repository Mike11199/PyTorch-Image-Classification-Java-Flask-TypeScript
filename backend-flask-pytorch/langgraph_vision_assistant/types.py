"""Shared data contracts using the frontend's existing JSON field names.

ViewerContext is validated HTTP input; AssistantResult is the browser response.
Framework-specific graph state is separate, in agent/state.py.
"""

from typing import Literal, TypeAlias
from typing_extensions import TypedDict
from pydantic import JsonValue

from .commands import ViewerCommand as ViewerCommand

Page: TypeAlias = Literal['boxes', 'mask', 'video']
PreparedCommand: TypeAlias = tuple[str, ViewerCommand]


class ViewerSnapshot(TypedDict):
    """Detected classes and settings supplied by the browser."""

    page: Page
    availableClasses: list[str]
    view: dict[str, JsonValue]


class ViewerContext(ViewerSnapshot):
    """Validated user request together with its viewer snapshot."""

    message: str


class AssistantResult(TypedDict):
    """Existing frontend response: commands to apply, or a clarification."""

    actions: list[ViewerCommand]
    message: str


class ErrorResponse(TypedDict):
    """User-facing HTTP failure, without backend exception details."""

    error: str
