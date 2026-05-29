from __future__ import annotations

from datetime import date, datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    created_at: datetime


class EmployeeShortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    position: str
    hired_at: date | None
    created_at: datetime


class DepartmentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    created_at: datetime
    employees: List[EmployeeShortResponse] = []
    children: List[DepartmentDetailResponse] = []


DepartmentDetailResponse.model_rebuild()
