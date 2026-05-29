from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import List


from models.employee import Employee


class DeleteMode(StrEnum):
    CASCADE = "cascade"
    REASSIGN = "reassign"


@dataclass
class CreateDepartmentDto:
    name: str
    parent_id: int | None


@dataclass
class UpdateDepartmentDto:
    name: str | None
    parent_id: int | None


@dataclass
class DeleteDepartmentDto:
    mode: DeleteMode
    reassign_to_department_id: int | None = None


@dataclass
class DepartmentDetailDto:
    id: int
    name: str
    parent_id: int | None
    created_at: datetime
    employees: List[Employee] = field(default_factory=list)
    children: List["DepartmentDetailDto"] = field(default_factory=list)
