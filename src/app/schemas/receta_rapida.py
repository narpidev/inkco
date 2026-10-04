from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, model_validator

Percentage = Annotated[
    Decimal,
    Field(gt=0, le=100, max_digits=6, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]
Grams = Annotated[
    Decimal,
    Field(ge=0, max_digits=12, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]


class RecetaComponentIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    component_name: str = Field(min_length=1, max_length=120)
    percentage: Percentage


class RecetaRapidaRequest(BaseModel):
    code: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=120)
    total_grs: Grams = Field(gt=0)
    components: list[RecetaComponentIn] = Field(min_length=1)

    @model_validator(mode="after")
    def check_percentage_sum(self):
        total = sum(c.percentage for c in self.components)
        if not (Decimal("99.5") <= total <= Decimal("100.5")):
            raise ValueError(f"Los % de los componentes suman {total}, deben sumar ~100")
        return self


class RecetaComponentOut(BaseModel):
    component_name: str
    percentage: Percentage
    grs: Grams


class RecetaRapidaResponse(BaseModel):
    code: str | None
    name: str | None
    total_grs: Grams
    components: list[RecetaComponentOut]