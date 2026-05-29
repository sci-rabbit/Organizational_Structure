import pytest
from httpx import AsyncClient


class TestCreateDepartment:
    async def test_create_root(self, client: AsyncClient):
        r = await client.post("/departments/", json={"name": "Engineering"})
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Engineering"
        assert data["parent_id"] is None
        assert "id" in data
        assert "created_at" in data

    async def test_create_child(self, client: AsyncClient):
        parent_id = (await client.post("/departments/", json={"name": "Engineering"})).json()["id"]
        r = await client.post("/departments/", json={"name": "Backend", "parent_id": parent_id})
        assert r.status_code == 201
        assert r.json()["parent_id"] == parent_id

    async def test_duplicate_name_same_parent_conflict(self, client: AsyncClient):
        parent_id = (await client.post("/departments/", json={"name": "Engineering"})).json()["id"]
        await client.post("/departments/", json={"name": "Backend", "parent_id": parent_id})
        r = await client.post("/departments/", json={"name": "Backend", "parent_id": parent_id})
        assert r.status_code == 409

    async def test_same_name_different_parents_allowed(self, client: AsyncClient):
        p1 = (await client.post("/departments/", json={"name": "Dept A"})).json()["id"]
        p2 = (await client.post("/departments/", json={"name": "Dept B"})).json()["id"]
        await client.post("/departments/", json={"name": "Backend", "parent_id": p1})
        r = await client.post("/departments/", json={"name": "Backend", "parent_id": p2})
        assert r.status_code == 201

    async def test_duplicate_root_names_conflict(self, client: AsyncClient):
        await client.post("/departments/", json={"name": "Engineering"})
        r = await client.post("/departments/", json={"name": "Engineering"})
        assert r.status_code == 409

    async def test_parent_not_found(self, client: AsyncClient):
        r = await client.post("/departments/", json={"name": "Backend", "parent_id": 9999})
        assert r.status_code == 404

    async def test_name_trimmed(self, client: AsyncClient):
        r = await client.post("/departments/", json={"name": "  Engineering  "})
        assert r.status_code == 201
        assert r.json()["name"] == "Engineering"

    async def test_empty_name_rejected(self, client: AsyncClient):
        r = await client.post("/departments/", json={"name": ""})
        assert r.status_code == 422

    async def test_name_too_long_rejected(self, client: AsyncClient):
        r = await client.post("/departments/", json={"name": "x" * 201})
        assert r.status_code == 422


class TestGetDepartment:
    async def test_not_found(self, client: AsyncClient):
        r = await client.get("/departments/9999")
        assert r.status_code == 404

    async def test_get_simple(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Engineering"})).json()["id"]
        r = await client.get(f"/departments/{dept_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == dept_id
        assert data["name"] == "Engineering"
        assert data["employees"] == []
        assert data["children"] == []

    async def test_depth_1_includes_direct_children_only(self, client: AsyncClient):
        root_id = (await client.post("/departments/", json={"name": "Root"})).json()["id"]
        child_id = (await client.post("/departments/", json={"name": "Child", "parent_id": root_id})).json()["id"]
        await client.post("/departments/", json={"name": "Grandchild", "parent_id": child_id})

        data = (await client.get(f"/departments/{root_id}?depth=1")).json()
        assert len(data["children"]) == 1
        assert data["children"][0]["id"] == child_id
        assert data["children"][0]["children"] == []

    async def test_depth_2_includes_grandchildren(self, client: AsyncClient):
        root_id = (await client.post("/departments/", json={"name": "Root"})).json()["id"]
        child_id = (await client.post("/departments/", json={"name": "Child", "parent_id": root_id})).json()["id"]
        gc_id = (await client.post("/departments/", json={"name": "GC", "parent_id": child_id})).json()["id"]

        data = (await client.get(f"/departments/{root_id}?depth=2")).json()
        assert data["children"][0]["children"][0]["id"] == gc_id

    async def test_depth_0_no_children(self, client: AsyncClient):
        root_id = (await client.post("/departments/", json={"name": "Root"})).json()["id"]
        await client.post("/departments/", json={"name": "Child", "parent_id": root_id})

        data = (await client.get(f"/departments/{root_id}?depth=0")).json()
        assert data["children"] == []

    async def test_depth_exceeds_max_rejected(self, client: AsyncClient):
        r = await client.get("/departments/1?depth=6")
        assert r.status_code == 422

    async def test_include_employees_true(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "HR"})).json()["id"]
        await client.post(f"/departments/{dept_id}/employees/", json={"full_name": "Alice", "position": "Manager"})

        data = (await client.get(f"/departments/{dept_id}?include_employees=true")).json()
        assert len(data["employees"]) == 1
        assert data["employees"][0]["full_name"] == "Alice"

    async def test_include_employees_false(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "HR"})).json()["id"]
        await client.post(f"/departments/{dept_id}/employees/", json={"full_name": "Alice", "position": "Manager"})

        data = (await client.get(f"/departments/{dept_id}?include_employees=false")).json()
        assert data["employees"] == []


class TestUpdateDepartment:
    async def test_update_name(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Old"})).json()["id"]
        r = await client.patch(f"/departments/{dept_id}", json={"name": "New"})
        assert r.status_code == 200
        assert r.json()["name"] == "New"

    async def test_update_parent(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Dept"})).json()["id"]
        parent_id = (await client.post("/departments/", json={"name": "Parent"})).json()["id"]
        r = await client.patch(f"/departments/{dept_id}", json={"parent_id": parent_id})
        assert r.status_code == 200
        assert r.json()["parent_id"] == parent_id

    async def test_self_reference_rejected(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Dept"})).json()["id"]
        r = await client.patch(f"/departments/{dept_id}", json={"parent_id": dept_id})
        assert r.status_code == 400

    async def test_cycle_detection(self, client: AsyncClient):
        root_id = (await client.post("/departments/", json={"name": "Root"})).json()["id"]
        child_id = (await client.post("/departments/", json={"name": "Child", "parent_id": root_id})).json()["id"]

        r = await client.patch(f"/departments/{root_id}", json={"parent_id": child_id})
        assert r.status_code == 400

    async def test_new_parent_not_found(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Dept"})).json()["id"]
        r = await client.patch(f"/departments/{dept_id}", json={"parent_id": 9999})
        assert r.status_code == 404

    async def test_department_not_found(self, client: AsyncClient):
        r = await client.patch("/departments/9999", json={"name": "New"})
        assert r.status_code == 404


class TestDeleteDepartment:
    async def test_cascade_deletes_subtree_and_employees(self, client: AsyncClient):
        root_id = (await client.post("/departments/", json={"name": "Root"})).json()["id"]
        child_id = (await client.post("/departments/", json={"name": "Child", "parent_id": root_id})).json()["id"]
        await client.post(f"/departments/{child_id}/employees/", json={"full_name": "Alice", "position": "Dev"})

        r = await client.delete(f"/departments/{root_id}?mode=cascade")
        assert r.status_code == 204
        assert (await client.get(f"/departments/{root_id}")).status_code == 404
        assert (await client.get(f"/departments/{child_id}")).status_code == 404

    async def test_reassign_moves_employees_and_deletes_dept(self, client: AsyncClient):
        source_id = (await client.post("/departments/", json={"name": "Source"})).json()["id"]
        target_id = (await client.post("/departments/", json={"name": "Target"})).json()["id"]
        await client.post(f"/departments/{source_id}/employees/", json={"full_name": "Alice", "position": "Dev"})

        r = await client.delete(
            f"/departments/{source_id}?mode=reassign&reassign_to_department_id={target_id}"
        )
        assert r.status_code == 204
        assert (await client.get(f"/departments/{source_id}")).status_code == 404

        target_data = (await client.get(f"/departments/{target_id}")).json()
        assert len(target_data["employees"]) == 1
        assert target_data["employees"][0]["full_name"] == "Alice"

    async def test_department_not_found(self, client: AsyncClient):
        r = await client.delete("/departments/9999?mode=cascade")
        assert r.status_code == 404

    async def test_reassign_without_target_rejected(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Dept"})).json()["id"]
        r = await client.delete(f"/departments/{dept_id}?mode=reassign")
        assert r.status_code == 400

    async def test_reassign_to_self_rejected(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Dept"})).json()["id"]
        r = await client.delete(f"/departments/{dept_id}?mode=reassign&reassign_to_department_id={dept_id}")
        assert r.status_code == 400

    async def test_reassign_target_not_found(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Dept"})).json()["id"]
        r = await client.delete(f"/departments/{dept_id}?mode=reassign&reassign_to_department_id=9999")
        assert r.status_code == 404

    async def test_invalid_mode_rejected(self, client: AsyncClient):
        dept_id = (await client.post("/departments/", json={"name": "Dept"})).json()["id"]
        r = await client.delete(f"/departments/{dept_id}?mode=invalid")
        assert r.status_code == 422
