from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_department_or_404
from core.database import get_ro_session, get_rw_session
from dto.department_dto import CreateDepartmentDto, DeleteMode, UpdateDepartmentDto
from dto.employee_dto import CreateEmployeeDto
from models.department import Department
from schemas.department import DepartmentCreate, DepartmentDetailResponse, DepartmentResponse, DepartmentUpdate
from schemas.employee import EmployeeCreate, EmployeeResponse
from services.department_service import DepartmentService
from services.employee_service import EmployeeService

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    body: DepartmentCreate,
    session: Annotated[AsyncSession, Depends(get_rw_session)],
):
    service = DepartmentService(session)
    return await service.create(CreateDepartmentDto(name=body.name, parent_id=body.parent_id))


@router.get("/{department_id}", response_model=DepartmentDetailResponse)
async def get_department(
    department_id: int,
    session: Annotated[AsyncSession, Depends(get_ro_session)],
    depth: Annotated[int, Query(ge=0, le=5)] = 1,
    include_employees: bool = True,
):
    service = DepartmentService(session)
    return await service.get(department_id, depth=depth, include_employees=include_employees)


@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    body: DepartmentUpdate,
    session: Annotated[AsyncSession, Depends(get_rw_session)],
    department: Annotated[Department, Depends(get_department_or_404)],
):
    service = DepartmentService(session)
    return await service.update(department, UpdateDepartmentDto(name=body.name, parent_id=body.parent_id))


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    mode: Annotated[DeleteMode, Query()],
    session: Annotated[AsyncSession, Depends(get_rw_session)],
    department: Annotated[Department, Depends(get_department_or_404)],
    reassign_to_department_id: Annotated[int | None, Query()] = None,
):
    service = DepartmentService(session)
    await service.delete(department, mode=mode, reassign_to_department_id=reassign_to_department_id)


@router.post("/{department_id}/employees/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    department_id: int,
    body: EmployeeCreate,
    session: Annotated[AsyncSession, Depends(get_rw_session)],
):
    service = EmployeeService(session)
    return await service.create(
        department_id,
        CreateEmployeeDto(full_name=body.full_name, position=body.position, hired_at=body.hired_at),
    )
