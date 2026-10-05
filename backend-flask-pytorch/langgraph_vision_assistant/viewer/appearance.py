"""Build color edits with the viewer's layer defaults and capability checks.

ClassColor describes one requested edit. The rules resolve CSS colors and
choose the browser target; omitted layers affect every layer the page supports.
"""

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from .checks import require_classes, require_masks
from .colors import color_hex
from .commands import ClassColorCommand
from .state import ViewerContext

Color = Annotated[str, Field(strict=True, min_length=1, max_length=80,
                              description='Requested CSS color name (such as red or teal), or a hex color.')]
Target = Literal['boxes', 'masks', 'both']
ColorLayers = Annotated[list[Literal['boxes', 'masks']], Field(min_length=1, max_length=2)]


class ClassColor(BaseModel):
    """One object's requested color and optional layer selection."""

    model_config = ConfigDict(extra='forbid')
    className: StrictStr
    color: Color
    layers: ColorLayers | None = None


def class_color_command(change: ClassColor, context: ViewerContext) -> ClassColorCommand:
    """Validate one color change and translate its layers to the browser target."""
    require_classes([change.className], context)
    target: Target = 'both'
    if change.layers == ['boxes']:
        target = 'boxes'
    elif change.layers == ['masks']:
        require_masks(context)
        target = 'masks'
    if context.page == 'boxes':
        target = 'boxes'
    return {'type': 'set_class_color', 'className': change.className,
            'color': color_hex(change.color), 'target': target}
