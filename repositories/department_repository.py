from typing import List

from sqlalchemy import select, literal, delete as sa_delete

from models.department import Department
from repositories.base_repository import AsyncRepository


class DepartmentRepository(AsyncRepository):
    model = Department

    async def get_subtree(self, root_id: int, max_depth: int) -> List[Department]:
        t = Department.__table__

        base = (
            select(t.c.id, literal(0).label("depth"))
            .where(t.c.id == root_id)
            .cte(name="subtree", recursive=True)
        )

        d = t.alias("d")
        recursive = (
            select(d.c.id, (base.c.depth + 1).label("depth"))
            .where(d.c.parent_id == base.c.id)
            .where(base.c.depth < max_depth)
        )

        cte = base.union_all(recursive)

        stmt = select(Department).where(Department.id.in_(select(cte.c.id)))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_ids_in_subtree(self, root_id: int) -> List[int]:
        t = Department.__table__

        anchor = select(t.c.id).where(t.c.id == root_id).cte(name="subtree", recursive=True)
        d = t.alias("d")
        recursive = select(d.c.id).where(d.c.parent_id == anchor.c.id)
        cte = anchor.union_all(recursive)

        result = await self.session.execute(select(cte.c.id))
        return list(result.scalars().all())

    async def delete_by_ids(self, ids: List[int]) -> None:
        await self.session.execute(sa_delete(Department).where(Department.id.in_(ids)))
