"""Define the dictionaries shared by the HTTP layer and the workflow.

ViewerContext carries validated user text and viewer settings into the graph.
AssistantResult carries edits or clarification text back to the route.
PreparedCommand pairs a tool's feedback with its list of browser edits.

These TypedDicts describe field names for type checking. Runtime validation lives
in api/schemas.py and tools/inputs.py; graph-specific fields live in agent/state.py.
The individual browser edit shapes are defined in commands.py.
"""

from typing import Literal, TypeAlias
from typing_extensions import TypedDict
from pydantic import JsonValue

from .commands import ViewerCommand as ViewerCommand

Page: TypeAlias = Literal['boxes', 'mask', 'video']
PreparedCommand: TypeAlias = tuple[str, list[ViewerCommand]]


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
