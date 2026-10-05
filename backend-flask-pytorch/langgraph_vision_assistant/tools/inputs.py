"""Strict tool argument types used by the functions in viewer.py.

LangChain derives JSON schemas from these annotations. Pydantic checks values
before a tool runs. Context is injected by LangGraph and hidden from the model;
it is not an argument the model can choose or replace.
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
