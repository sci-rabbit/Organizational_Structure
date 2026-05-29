import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from dto.department_dto import (
    CreateDepartmentDto,
    DeleteDepartmentDto,
    DeleteMode,
    DepartmentDetailDto,
    UpdateDepartmentDto,
)
from exceptions.department import (
    DepartmentAlreadyExists,
    DepartmentNotFound,
    DepartmentParentConflict,
    DepartmentReassignConflict,
)
from models.department import Department
from repositories.department_repository import DepartmentRepository
from repositories.employee_repository import EmployeeRepository


class DepartmentService:
    def __init__(self, session: AsyncSession):
        self.department_repo = DepartmentRepository(session)
        self.employee_repo = EmployeeRepository(session)

    async def create(self, department_dto: CreateDepartmentDto) -> Department:
        if department_dto.parent_id is not None:
            parent = await self.department_repo.get(department_dto.parent_id)

            if parent is None:
                raise DepartmentNotFound()

        existing = await self.department_repo.get_one_by(
            parent_id=department_dto.parent_id,
            name=department_dto.name,
        )
        if existing is not None:
            raise DepartmentAlreadyExists()

        department = await self.department_repo.create(
            name=department_dto.name,
            parent_id=department_dto.parent_id,
        )

        if department.id == department_dto.parent_id:
            raise DepartmentParentConflict()

        logger.info("Department created: id=%d, name=%r, parent_id=%s", department.id, department.name, department.parent_id)
        return department

    async def get(
        self,
        department_id: int,
        depth: int = 1,
        include_employees: bool = True,
    ) -> DepartmentDetailDto:
        all_depts = await self.department_repo.get_subtree(
            department_id, max_depth=depth
        )
        if not all_depts:
            raise DepartmentNotFound()

        dept_map = {d.id: d for d in all_depts}

        employees_by_dept: dict[int, list] = {}
        if include_employees:
            employees = await self.employee_repo.list_by_department_ids(
                list(dept_map.keys())
            )
            for emp in employees:
                employees_by_dept.setdefault(emp.department_id, []).append(emp)

        def build_node(dept_id: int) -> DepartmentDetailDto:
            dept = dept_map[dept_id]
            children = [build_node(d.id) for d in all_depts if d.parent_id == dept_id]
            return DepartmentDetailDto(
                id=dept.id,
                name=dept.name,
                parent_id=dept.parent_id,
                created_at=dept.created_at,
                employees=employees_by_dept.get(dept_id, []),
                children=children,
            )

        result = build_node(department_id)
        logger.debug("Department fetched: id=%d, depth=%d, nodes=%d", department_id, depth, len(all_depts))
        return result

    async def update(
        self, department: Department, department_dto: UpdateDepartmentDto
    ) -> Department:
        new_parent_id = department_dto.parent_id

        if new_parent_id is not None:
            if new_parent_id == department.id:
                raise DepartmentParentConflict()

            subtree_ids = await self.department_repo.get_all_ids_in_subtree(department.id)
            if new_parent_id in subtree_ids:
                raise DepartmentParentConflict()

            parent = await self.department_repo.get(new_parent_id)
            if parent is None:
                raise DepartmentNotFound()

        department_data = {
            k: v for k, v in department_dto.__dict__.items() if v is not None
        }
        updated = await self.department_repo.update(department, department_data)
        logger.info("Department updated: id=%d, changes=%s", department.id, list(department_data.keys()))
        return updated

    async def delete(
        self,
        department: Department,
        mode: DeleteMode,
        reassign_to_department_id: int | None = None,
    ) -> None:
        if mode == DeleteMode.CASCADE:
            ids = await self.department_repo.get_all_ids_in_subtree(department.id)
            await self.department_repo.delete_by_ids(ids)
            logger.info("Department deleted (cascade): root_id=%d, total_deleted=%d", department.id, len(ids))
        else:
            if reassign_to_department_id is None:
                raise DepartmentReassignConflict()

            if reassign_to_department_id == department.id:
                raise DepartmentReassignConflict()

            target = await self.department_repo.get(reassign_to_department_id)
            if target is None:
                raise DepartmentNotFound()

            await self.employee_repo.reassign_to_department(department.id, reassign_to_department_id)
            await self.department_repo.delete(department)
            logger.info("Department deleted (reassign): id=%d, employees_moved_to=%d", department.id, reassign_to_department_id)
