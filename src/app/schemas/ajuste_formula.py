from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

LabValue = Annotated[
    Decimal,
    Field(max_digits=7, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]
DeltaValue = Annotated[
    Decimal,
    Field(max_digits=9, decimal_places=4),
    PlainSerializer(float, return_type=float, when_used="json"),
]
Grams = Annotated[
    Decimal,
    Field(max_digits=10, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]


class LabPoint(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    l: LabValue
    a: LabValue
    b: LabValue


class AjusteFormulaRequest(BaseModel):
    component_name: str = Field(min_length=1, max_length=120)
    lab_target: LabPoint
    lab_before: LabPoint   # lectura antes de agregar la dosis de prueba
    lab_after: LabPoint    # lectura después de agregar grams_added
    grams_added: Grams = Field(gt=0)  # cuánto agregaste entre "before" y "after"


class EjeAjuste(BaseModel):
    eje: Literal["L", "a", "b"]
    sensibilidad_por_gramo: DeltaValue  # cuánto se mueve el eje por cada gramo agregado
    delta_restante: DeltaValue          # lo que falta para llegar al objetivo en ese eje
    grs_sugeridos: Grams | None         # None si el componente no mueve este eje
    overshoot: bool                     # True si grs_sugeridos salió negativo (ya te pasaste)


class AjusteFormulaResponse(BaseModel):
    component_name: str
    delta_e_antes: DeltaValue
    delta_e_despues: DeltaValue
    ejes: list[EjeAjuste]
    eje_dominante: Literal["a", "b"]  # cambia de Literal["L", "a", "b"] a solo estos dos
    grs_sugeridos: Grams | None
    advertencia: str | None = None   # nuevo