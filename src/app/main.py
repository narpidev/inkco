from fastapi import FastAPI

from app.api.routers import auth, formulas, inventario, recetas
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth.router)
app.include_router(inventario.router)
app.include_router(formulas.router)
app.include_router(recetas.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}