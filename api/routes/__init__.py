from fastapi import APIRouter

from api.routes.departments import router as departments_router

router = APIRouter()
router.include_router(departments_router)
