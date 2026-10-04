from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer

Percentage = Annotated[
    Decimal,
    Field(max_digits=6, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]
Grams = Annotated[
    Decimal,
    Field(max_digits=12, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]


class PrepararMezclaRequest(BaseModel):
    total_grs: Grams = Field(gt=0)


class ComponentePreparado(BaseModel):
    component_name: str
    percentage: Percentage
    grs: Grams


class PrepararMezclaResponse(BaseModel):
    formula_id: int
    code: str
    name: str
    total_grs: Grams
    components: list[ComponentePreparado]