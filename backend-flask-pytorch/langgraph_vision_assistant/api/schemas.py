"""Describe the JSON fields accepted from the browser.

request.py validates parsed JSON with AssistantRequest. Pydantic checks field
types and limits; the validators trim text, deduplicate class names, and bound
the viewer settings. Invalid data raises a validation error before inference.

to_context returns the dictionary used by the graph, preserving the browser's
field names. HTTP body limits and error responses are handled by request.py.
"""

import json
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StringConstraints, field_validator

from ..types import Page, ViewerContext

Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
Category = Annotated[str, StringConstraints(pattern=r'^[a-z][a-z -]{0,39}$')]


class AssistantRequest(BaseModel):
    """User text plus the detected classes and settings of the current viewer."""

    model_config = ConfigDict(strict=True)

    message: Message
    page: Page
    availableClasses: list[Category] = Field(max_length=80)
    view: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator('availableClasses')
    @classmethod
    def unique_classes(cls, classes: list[str]) -> list[str]:
        """Give tools a stable, duplicate-free list of detected classes."""
        return sorted(set(classes))

    @field_validator('view')
    @classmethod
    def bounded_view(cls, view: dict[str, JsonValue]) -> dict[str, JsonValue]:
        """Reject nonfinite numbers and snapshots larger than the existing limit."""
        if len(json.dumps(view, allow_nan=False)) > 3000:
            raise ValueError('Invalid viewer state.')
        return view

    def to_context(self) -> ViewerContext:
        """Keep the existing browser field names when entering the graph."""
        return {'message': self.message, 'page': self.page,
                'availableClasses': self.availableClasses, 'view': self.view}
