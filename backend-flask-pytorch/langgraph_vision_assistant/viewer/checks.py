"""Check whether a requested edit makes sense in the current viewer.

The tool argument types check formats and ranges. These functions check
facts from the request, such as whether a class was detected or masks are
available on this page. Viewer rules call them before preparing an edit.

A failed check raises ValueError. ToolNode turns that into tool feedback, and
the graph gives Qwen another attempt without applying any edits from this one.
"""

from collections.abc import Sequence
from .state import ViewerContext


def require_classes(classes: Sequence[str], context: ViewerContext) -> None:
    """Reject class names that are absent from the current detection results."""
    for name in classes:
        if name not in context.available_classes:
            raise ValueError(f'{name} is not detected. Available classes: {context.available_classes}.')


def require_masks(context: ViewerContext) -> None:
    """Reject mask operations in the Faster R-CNN boxes viewer."""
    if context.page == 'boxes':
        raise ValueError('This viewer has no masks. Use boxes only.')

