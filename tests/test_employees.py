import pytest
from httpx import AsyncClient


class TestCreateEmployee:
    async def test_create_employee(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Engineering"})).json()["id"]
        r = await client.post(
            f"/departments/{dept_id}/employees/",
            json={"full_name": "Alice Smith", "position": "Engineer"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["full_name"] == "Alice Smith"
        assert data["position"] == "Engineer"
        assert data["department_id"] == dept_id
        assert data["hired_at"] is None
        assert "id" in data
        assert "created_at" in data

    async def test_create_employee_with_hired_at(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "HR"})).json()["id"]
        r = await client.post(
            f"/departments/{dept_id}/employees/",
            json={"full_name": "Bob Jones", "position": "Manager", "hired_at": "2024-01-15"},
        )
        assert r.status_code == 201
        assert r.json()["hired_at"] == "2024-01-15"

    async def test_department_not_found(self, client: AsyncClient):
        r = await client.post(
            "/departments/9999/employees/",
            json={"full_name": "Alice", "position": "Dev"},
        )
        assert r.status_code == 404

    async def test_empty_full_name_rejected(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "HR"})).json()["id"]
        r = await client.post(
            f"/departments/{dept_id}/employees/",
            json={"full_name": "", "position": "Manager"},
        )
        assert r.status_code == 422

    async def test_empty_position_rejected(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "HR"})).json()["id"]
        r = await client.post(
            f"/departments/{dept_id}/employees/",
            json={"full_name": "Alice", "position": ""},
        )
        assert r.status_code == 422

    async def test_name_trimmed(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "HR"})).json()["id"]
        r = await client.post(
            f"/departments/{dept_id}/employees/",
            json={"full_name": "  Alice  ", "position": "  Manager  "},
        )
        assert r.status_code == 201
        assert r.json()["full_name"] == "Alice"
        assert r.json()["position"] == "Manager"

    async def test_employees_appear_in_department(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Engineering"})).json()["id"]
        await client.post(f"/departments/{dept_id}/employees/", json={"full_name": "Alice", "position": "Dev"})
        await client.post(f"/departments/{dept_id}/employees/", json={"full_name": "Bob", "position": "QA"})

        data = (await client.get(f"/departments/{dept_id}")).json()
        assert len(data["employees"]) == 2
        names = {e["full_name"] for e in data["employees"]}
        assert names == {"Alice", "Bob"}
