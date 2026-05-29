from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_rw_session
from exceptions.department import DepartmentNotFound
from models.department import Department
from repositories.department_repository import DepartmentRepository


async def get_department_or_404(
    department_id: int,
    session: Annotated[AsyncSession, Depends(get_rw_session)],
) -> Department:
    repo = DepartmentRepository(session)
    department = await repo.get(department_id)
    if department is None:
        raise DepartmentNotFound()
    return department
