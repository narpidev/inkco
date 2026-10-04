from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, model_validator

Grams = Annotated[
    Decimal,
    Field(max_digits=12, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]
Percentage = Annotated[
    Decimal,
    Field(max_digits=6, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]


class DesgloseComponentIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    component_name: str = Field(min_length=1, max_length=120)
    grs: Grams = Field(gt=0)


class DesgloseFormulaRequest(BaseModel):
    code: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=120)
    total_grs: Grams | None = Field(default=None, gt=0)
    components: list[DesgloseComponentIn] = Field(min_length=1)

    @model_validator(mode="after")
    def resolve_total(self):
        suma = sum(c.grs for c in self.components)
        if self.total_grs is None:
            # No lo diste: lo tomamos como la suma de los componentes
            self.total_grs = suma.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        else:
            # Lo diste (ej. lo que marcó la balanza): validamos que cuadre,
            # con tolerancia del 2% para redondeos de pesaje
            tolerancia = max(suma * Decimal("0.02"), Decimal("0.5"))
            if abs(self.total_grs - suma) > tolerancia:
                raise ValueError(
                    f"La suma de los componentes ({suma}) no coincide con el "
                    f"total indicado ({self.total_grs})"
                )
        return self


class DesgloseComponentOut(BaseModel):
    component_name: str
    grs: Grams
    percentage: Percentage


class DesgloseFormulaResponse(BaseModel):
    code: str | None
    name: str | None
    total_grs: Grams
    components: list[DesgloseComponentOut]