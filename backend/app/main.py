from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 基础框架不引入迁移工具，启动时按模型建表；后续接正式业务时再换 Alembic
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="平台基础框架", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(api_router, prefix="/api/v1")
