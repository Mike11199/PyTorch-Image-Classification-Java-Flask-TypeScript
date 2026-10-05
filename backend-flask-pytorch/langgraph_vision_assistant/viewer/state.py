"""Validate the viewer settings read by command-building functions.

The service creates one ViewerContext per request. Rules use its typed view;
the prompt uses the original snapshot so field order and unrelated settings
stay exactly as the browser supplied them. Missing settings have no defaults.
"""

from dataclasses import dataclass, field
from typing import Literal
from typing_extensions import TypedDict

from pydantic import BaseModel, Field, JsonValue, StrictBool, StrictStr

Page = Literal['boxes', 'mask', 'video']


class ViewerRequest(TypedDict):
    """Validated request fields before viewer settings become typed objects."""

    message: str
    page: Page
    availableClasses: list[str]
    view: dict[str, JsonValue]


class LayerToggle(BaseModel):
    """Visibility of a layer; display settings remain in the original snapshot."""

    enabled: StrictBool


class ViewerLayers(BaseModel):
    """The three visibility flags supplied together by the browser."""

    boxes: LayerToggle
    masks: LayerToggle
    labels: LayerToggle


class ViewerFilters(BaseModel):
    """An empty selection shows all classes; None hides all classes."""

    visible_classes: list[StrictStr] | None = Field(alias='visibleClasses')


class ViewerSettings(BaseModel):
    """Settings read by viewer rules; absent sections remain unavailable."""

    layers: ViewerLayers | None = None
    filters: ViewerFilters | None = None

    def require_layers(self) -> ViewerLayers:
        """Require actual layer settings instead of guessing their visibility."""
        if self.layers is None:
            raise ValueError('Current layer settings are required.')
        return self.layers

    def require_filters(self) -> ViewerFilters:
        """Require the browser's selection before changing part of it."""
        if self.filters is None:
            raise ValueError('Current class filter settings are required.')
        return self.filters


@dataclass(frozen=True)
class ViewerContext:
    """User request and typed viewer state, shared by the workflow and rules."""

    message: str
    page: Page
    available_classes: list[str]
    view: ViewerSettings
    _raw_view: dict[str, JsonValue] = field(repr=False)

    @classmethod
    def from_request(cls, request: ViewerRequest) -> 'ViewerContext':
        """Validate settings once while retaining the model's original input."""
        return cls(message=request['message'], page=request['page'],
                   available_classes=request['availableClasses'],
                   view=ViewerSettings.model_validate(request['view']),
                   _raw_view=request['view'])

    def prompt_snapshot(self) -> dict[str, JsonValue]:
        """Return the original browser field names, values, and ordering."""
        return {'page': self.page, 'availableClasses': list(self.available_classes),
                'view': self._raw_view}
