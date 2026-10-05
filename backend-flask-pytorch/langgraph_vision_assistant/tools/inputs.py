"""Define the accepted arguments for the tools in viewer.py.

LangChain turns these annotations into schemas describing each tool to Qwen.
Pydantic uses the same constraints to check values before execution, including
hex colors, numeric ranges, and allowed selection modes.

Context is different: LangGraph supplies it from the request's state. Qwen does
not choose it. It contains the actual viewer page and detected classes, which
tools/checks.py uses to validate whether an operation is available.
"""

from typing import Annotated, Literal

from langgraph.prebuilt import InjectedState
from pydantic import Field, StrictStr

from ..types import ViewerContext

Context = Annotated[ViewerContext, InjectedState('context')]
Classes = Annotated[list[StrictStr], Field(strict=True, max_length=80)]
Color = Annotated[str, Field(strict=True, pattern=r'^#[0-9a-fA-F]{6}$', max_length=7)]
Fraction = Annotated[float, Field(strict=True, ge=0, le=1, allow_inf_nan=False)]
Target = Literal['boxes', 'masks', 'both']
Region = Literal['all', 'left', 'right']
Selection = Literal['leftmost', 'rightmost', 'largest', 'least_confident']
Seek = Literal['first', 'next', 'peak']
