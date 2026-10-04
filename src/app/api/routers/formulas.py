from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user, get_db
from app.models.formula import Formula, FormulaComponent
from app.models.user import User
from app.schemas.formula import FormulaCreate, FormulaRead, FormulaUpdate
from app.schemas.preparar_mezcla import PrepararMezclaRequest, PrepararMezclaResponse
from app.services.mezclas import calcular_gramos_por_porcentaje
from app.schemas.desglose_formula import DesgloseFormulaRequest, DesgloseFormulaResponse
from app.services.mezclas import calcular_gramos_por_porcentaje, calcular_porcentaje_por_gramos
from app.schemas.ajuste_formula import AjusteFormulaRequest, AjusteFormulaResponse, EjeAjuste
from app.services.colorimetria import calcular_ajuste_componente, calcular_delta_e76

router = APIRouter(prefix="/formulas", tags=["formulas"])


async def _get_owned_formula(formula_id: int, user: User, db: AsyncSession) -> Formula:
    formula = await db.scalar(
        select(Formula)
        .options(selectinload(Formula.components))
        .where(Formula.id == formula_id, Formula.user_id == user.id)
    )
    if formula is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fórmula no encontrada")
    return formula


@router.get("", response_model=list[FormulaRead])
async def list_formulas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Formula)
        .where(Formula.user_id == current_user.id)
        .order_by(Formula.name)
    )
    result = await db.scalars(stmt)
    return result.all()


@router.post("", response_model=FormulaRead, status_code=status.HTTP_201_CREATED)
async def create_formula(
    data: FormulaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    formula = Formula(
        code=data.code,
        name=data.name,
        user_id=current_user.id,
        components=[
            FormulaComponent(**c.model_dump()) for c in data.components
        ],
    )
    db.add(formula)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya tienes una fórmula con ese código")
    await db.refresh(formula, attribute_names=["updated_at", "components"])
    return formula

@router.post("/desglosar", response_model=DesgloseFormulaResponse)
async def desglosar_formula(
    data: DesgloseFormulaRequest,
    current_user: User = Depends(get_current_user),
):
    componentes = calcular_porcentaje_por_gramos(
        data.total_grs,
        [(c.component_name, c.grs) for c in data.components],
    )
    return DesgloseFormulaResponse(
        code=data.code,
        name=data.name,
        total_grs=data.total_grs,
        components=componentes,
    )

@router.post("/calibrar-ajuste", response_model=AjusteFormulaResponse)
async def calibrar_ajuste(
    data: AjusteFormulaRequest,
    current_user: User = Depends(get_current_user),
):
    target = (data.lab_target.l, data.lab_target.a, data.lab_target.b)
    before = (data.lab_before.l, data.lab_before.a, data.lab_before.b)
    after = (data.lab_after.l, data.lab_after.a, data.lab_after.b)

    ejes_calculados = calcular_ajuste_componente(target, before, after, data.grams_added)

    # L se excluye de la decisión: es sensible al grosor de capa, no a la composición
    ejes_relevantes = [e for e in ejes_calculados if e["eje"] in ("a", "b")]
    eje_dominante_data = max(ejes_relevantes, key=lambda e: abs(e["sensibilidad_por_gramo"]))

    advertencia = None
    if eje_dominante_data["overshoot"]:
        advertencia = (
            f"Ya superaste el objetivo en el eje {eje_dominante_data['eje']} "
            f"agregando {data.component_name}. Agregar más no ayuda — prueba con "
            f"un componente opuesto: agrégalo, mide"
        )

    return AjusteFormulaResponse(
        component_name=data.component_name,
        delta_e_antes=calcular_delta_e76(before, target),
        delta_e_despues=calcular_delta_e76(after, target),
        ejes=[EjeAjuste(**e) for e in ejes_calculados],
        eje_dominante=eje_dominante_data["eje"],
        grs_sugeridos=eje_dominante_data["grs_sugeridos"],
        advertencia=advertencia,
    )
        
@router.get("/{formula_id}", response_model=FormulaRead)
async def get_formula(
    formula_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_owned_formula(formula_id, current_user, db)


@router.patch("/{formula_id}", response_model=FormulaRead)
async def update_formula(
    formula_id: int,
    data: FormulaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    formula = await _get_owned_formula(formula_id, current_user, db)

    if data.code is not None:
        formula.code = data.code
    if data.name is not None:
        formula.name = data.name
    if data.components is not None:
        # cascade="all, delete-orphan" hace que esta asignación borre los
        # componentes viejos y guarde los nuevos al hacer commit.
        formula.components = [
            FormulaComponent(**c.model_dump()) for c in data.components
        ]

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya tienes una fórmula con ese código")
    await db.refresh(formula, attribute_names=["updated_at", "components"])
    return formula


@router.delete("/{formula_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_formula(
    formula_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    formula = await _get_owned_formula(formula_id, current_user, db)
    await db.delete(formula)
    await db.commit()
    
@router.post("/{formula_id}/preparar", response_model=PrepararMezclaResponse)
async def preparar_mezcla(
    formula_id: int,
    data: PrepararMezclaRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    formula = await _get_owned_formula(formula_id, current_user, db)

    componentes = calcular_gramos_por_porcentaje(
        data.total_grs,
        [(c.component_name, c.percentage) for c in formula.components],
    )

    return PrepararMezclaResponse(
        formula_id=formula.id,
        code=formula.code,
        name=formula.name,
        total_grs=data.total_grs,
        components=componentes,
    )