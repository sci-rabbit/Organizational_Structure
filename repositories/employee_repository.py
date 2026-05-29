from sqlalchemy import select, update as sa_update

from models.employee import Employee
from repositories.base_repository import AsyncRepository


class EmployeeRepository(AsyncRepository):
    model = Employee

    async def list_by_department_ids(self, department_ids: list[int]) -> list[Employee]:
        stmt = (
            select(Employee)
            .where(Employee.department_id.in_(department_ids))
            .order_by(Employee.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def reassign_to_department(self, from_dept_id: int, to_dept_id: int) -> None:
        stmt = (
            sa_update(Employee)
            .where(Employee.department_id == from_dept_id)
            .values(department_id=to_dept_id)
        )
        await self.session.execute(stmt)
