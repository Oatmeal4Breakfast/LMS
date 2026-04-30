from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager

from src.dependencies.config import get_config, Config, EnvType
from src.core.logging import config_logger, get_logger
from src.routers.v1 import users

config_logger(get_config())

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(router=users.router, prefix="/api/v1")


@app.middleware("http")
async def log_request(request: Request, call_next):
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        client=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
    )
    response = await call_next(request)
    logger.info("response", status_code=response.status_code)
    return response


@app.get("/")
def index():
    return {"Hello": "World"}
