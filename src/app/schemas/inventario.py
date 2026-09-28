from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

# Decimal en Python, pero número (no string) en el JSON de salida.
# Sin el serializer, Pydantic v2 devuelve "100.500" como string.
Grams = Annotated[
    Decimal,
    Field(ge=0, max_digits=12, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]


class InventoryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=120)
    quantity_grs: Grams = Decimal("0")
    location: str | None = Field(default=None, max_length=120)
    comment: str | None = None


class InventoryUpdate(BaseModel):
    """Todos los campos opcionales: solo se modifica lo que se envía (PATCH)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    quantity_grs: Grams | None = None
    location: str | None = Field(default=None, max_length=120)
    comment: str | None = None

    @field_validator("code", "name", "quantity_grs")
    @classmethod
    def not_null(cls, v):
        # Estos campos no admiten NULL en la DB; omitirlos está bien, enviarlos null no.
        if v is None:
            raise ValueError("Este campo no puede ser null")
        return v


class InventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    quantity_grs: Grams
    location: str | None
    comment: str | None
    created_at: datetime
    updated_at: datetime