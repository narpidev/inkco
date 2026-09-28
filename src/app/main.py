from fastapi import FastAPI

from app.api.routers import auth
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}