import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from api.routes import router
from core.database import dispose
from exceptions.base import BaseAppException

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await dispose()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(BaseAppException)
async def app_exception_handler(request, exc: BaseAppException):
    if exc.status_code >= 500:
        logger.error("Unhandled exception on %s: %s", request.url.path, exc.detail, exc_info=exc)
    else:
        logger.warning("Client error %d on %s: %s", exc.status_code, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.include_router(router)
