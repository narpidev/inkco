from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.inventario import InventoryItem
from app.models.user import User
from app.schemas.inventario import InventoryCreate, InventoryRead, InventoryUpdate

router = APIRouter(prefix="/inventario", tags=["inventario"])


async def _get_owned_item(item_id: int, user: User, db: AsyncSession) -> InventoryItem:
    item = await db.scalar(
        select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.user_id == user.id,
        )
    )
    if item is None:
        # 404 y no 403: no revelamos si el ítem existe pero es de otro usuario
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ítem no encontrado")
    return item


@router.get("", response_model=list[InventoryRead])
async def list_items(
    q: str | None = Query(default=None, min_length=1, max_length=50),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(InventoryItem).where(InventoryItem.user_id == current_user.id)
    if q:
        stmt = stmt.where(
            or_(
                InventoryItem.code.icontains(q, autoescape=True),
                InventoryItem.name.icontains(q, autoescape=True),
            )
        )
    stmt = stmt.order_by(InventoryItem.name).limit(limit).offset(offset)
    result = await db.scalars(stmt)
    return result.all()


@router.post("", response_model=InventoryRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    data: InventoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = InventoryItem(**data.model_dump(), user_id=current_user.id)
    db.add(item)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya tienes un ítem con ese código")
    await db.refresh(item)
    return item


@router.get("/{item_id}", response_model=InventoryRead)
async def get_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_owned_item(item_id, current_user, db)


@router.patch("/{item_id}", response_model=InventoryRead)
async def update_item(
    item_id: int,
    data: InventoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_owned_item(item_id, current_user, db)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya tienes un ítem con ese código")
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_owned_item(item_id, current_user, db)
    await db.delete(item)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)