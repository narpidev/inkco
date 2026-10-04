from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, model_validator

Percentage = Annotated[
    Decimal,
    Field(gt=0, le=100, max_digits=6, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]
LabValue = Annotated[
    Decimal,
    Field(max_digits=6, decimal_places=3),
    PlainSerializer(float, return_type=float, when_used="json"),
]


class ComponentIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    component_name: str = Field(min_length=1, max_length=120)
    percentage: Percentage
    lab_l: LabValue | None = None
    lab_a: LabValue | None = None
    lab_b: LabValue | None = None
    delta_e: LabValue | None = None
    lab_source: str | None = Field(default=None, max_length=50)


class ComponentRead(ComponentIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class FormulaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=120)
    components: list[ComponentIn] = Field(min_length=1)

    @model_validator(mode="after")
    def check_percentage_sum(self):
        total = sum(c.percentage for c in self.components)
        if not (Decimal("99.5") <= total <= Decimal("100.5")):
            raise ValueError(f"Los % de los componentes suman {total}, deben sumar ~100")
        return self


class FormulaUpdate(BaseModel):
    """Reemplaza nombre/código si se envían, y la lista completa de componentes si se envía."""

    model_config = ConfigDict(str_strip_whitespace=True)

    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    components: list[ComponentIn] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def check_percentage_sum(self):
        if self.components is not None:
            total = sum(c.percentage for c in self.components)
            if not (Decimal("99.5") <= total <= Decimal("100.5")):
                raise ValueError(f"Los % de los componentes suman {total}, deben sumar ~100")
        return self


class FormulaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    components: list[ComponentRead]
    created_at: datetime
    updated_at: datetime