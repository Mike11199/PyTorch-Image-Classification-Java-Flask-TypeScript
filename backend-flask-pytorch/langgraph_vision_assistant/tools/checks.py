"""Check viewer capabilities that cannot be expressed by argument types.

The input schemas validate values; these checks compare them with the current
page and detected classes. Tools call them before preparing any browser edit.
"""

from collections.abc import Sequence
from ..types import ViewerContext


def require_classes(classes: Sequence[str], context: ViewerContext) -> None:
    """Reject class names that are absent from the current detection results."""
    for name in classes:
        if name not in context['availableClasses']:
            raise ValueError(f'{name} is not detected. Available classes: {context["availableClasses"]}.')


def require_masks(context: ViewerContext) -> None:
    """Reject mask operations in the Faster R-CNN boxes viewer."""
    if context['page'] == 'boxes':
        raise ValueError('This viewer has no masks. Use boxes only.')

