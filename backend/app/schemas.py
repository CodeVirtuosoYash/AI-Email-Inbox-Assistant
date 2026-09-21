"""Pydantic request bodies. Responses are plain dicts built in crud.py/rollup.py
— they flatten fields across Email/Analysis/Task/Reply (e.g. email_subject)
to match the frontend's expected shape, which doesn't map 1:1 to any single
ORM model, so response_model validation would fight the shape more than help.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class TaskPatchIn(BaseModel):
    status: Literal["pending", "done"]


class RegenerateIn(BaseModel):
    tone: str = "friendly"
