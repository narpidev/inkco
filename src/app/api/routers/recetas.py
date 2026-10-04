from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.receta_rapida import RecetaRapidaRequest, RecetaRapidaResponse
from app.services.mezclas import calcular_gramos_por_porcentaje

router = APIRouter(prefix="/recetas", tags=["recetas"])


@router.post("/rapida", response_model=RecetaRapidaResponse)
async def receta_rapida(
    data: RecetaRapidaRequest,
    current_user: User = Depends(get_current_user),  # exige login, no toca la DB
):
    componentes = calcular_gramos_por_porcentaje(
        data.total_grs,
        [(c.component_name, c.percentage) for c in data.components],
    )
    return RecetaRapidaResponse(
        code=data.code,
        name=data.name,
        total_grs=data.total_grs,
        components=componentes,
    )