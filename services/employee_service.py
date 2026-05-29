import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from dto.employee_dto import CreateEmployeeDto
from exceptions.department import DepartmentNotFound
from models.employee import Employee
from repositories.department_repository import DepartmentRepository
from repositories.employee_repository import EmployeeRepository


class EmployeeService:
    def __init__(self, session: AsyncSession):
        self.employee_repo = EmployeeRepository(session)
        self.department_repo = DepartmentRepository(session)

    async def create(
        self, department_id: int, employee_dto: CreateEmployeeDto
    ) -> Employee:
        department = await self.department_repo.get(department_id)

        if department is None:
            raise DepartmentNotFound()

        employee = await self.employee_repo.create(
            department_id=department_id,
            full_name=employee_dto.full_name,
            position=employee_dto.position,
            hired_at=employee_dto.hired_at,
        )
        logger.info("Employee created: id=%d, department_id=%d, full_name=%r", employee.id, employee.department_id, employee.full_name)
        return employee
