"""Exact JSON commands understood by the browser's existing executor.

Each TypedDict names the required fields of one command. Tools validate their
inputs with Pydantic, then construct these typed dictionaries. Keeping commands
as dictionaries preserves the API and avoids serializing internal model objects
through LangGraph's tool artifacts.
"""

from typing import Literal, TypeAlias
from typing_extensions import TypedDict


class VisibleClassesCommand(TypedDict):
    """Show only the requested classes."""

    type: Literal['set_visible_classes']
    classes: list[str]


class ClassColorCommand(TypedDict):
    """Change the color of one detected class."""

    type: Literal['set_class_color']
    className: str
    color: str
    target: Literal['boxes', 'masks', 'both']


class ConfidenceCommand(TypedDict):
    """Set the minimum confidence shown."""

    type: Literal['set_confidence']
    value: float


class MaskOpacityCommand(TypedDict):
    """Change mask transparency."""

    type: Literal['set_mask_opacity']
    value: float


class LayersCommand(TypedDict):
    """Choose which overlay layers are visible."""

    type: Literal['set_layers']
    boxes: bool
    masks: bool
    labels: bool


class CountCommand(TypedDict):
    """Ask the browser to count detections."""

    type: Literal['count_detections']
    classes: list[str]
    region: Literal['all', 'left', 'right']


class SelectCommand(TypedDict):
    """Highlight a detection using a selection rule."""

    type: Literal['select_detection']
    className: str
    mode: Literal['leftmost', 'rightmost', 'largest', 'least_confident']


class SeekCommand(TypedDict):
    """Move video playback to a matching detection."""

    type: Literal['seek_detection']
    className: str
    mode: Literal['first', 'next', 'peak']


class ResetCommand(TypedDict):
    """Restore the default viewer settings."""

    type: Literal['reset_view']


ViewerCommand: TypeAlias = (
    VisibleClassesCommand
    | ClassColorCommand
    | ConfidenceCommand
    | MaskOpacityCommand
    | LayersCommand
    | CountCommand
    | SelectCommand
    | SeekCommand
    | ResetCommand
)
