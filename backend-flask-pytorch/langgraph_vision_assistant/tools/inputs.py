"""Describe the arguments exposed to Qwen by the tool wrappers.

LangChain turns these annotations into tool schemas; Pydantic checks their
constraints. Context is injected from graph state and never chosen by Qwen.
Viewer settings and behavior live in viewer/, independently of these schemas.
"""

from typing import Annotated, Literal

from langgraph.prebuilt import InjectedState
from pydantic import Field, StrictStr

from ..viewer.state import ViewerContext
from ..viewer.appearance import ClassColor
from ..viewer.detections import Region as Region, Seek as Seek, Selection as Selection

Context = Annotated[ViewerContext, InjectedState('context')]
Classes = Annotated[list[StrictStr], Field(strict=True, max_length=80)]
Fraction = Annotated[float, Field(strict=True, ge=0, le=1, allow_inf_nan=False)]
Layers = Annotated[list[Literal['boxes', 'masks', 'labels']], Field(max_length=3)]
ClassColors = Annotated[list[ClassColor], Field(min_length=1, max_length=80)]
