import math
from decimal import ROUND_HALF_UP, Decimal

EJES = ("L", "a", "b")


def calcular_delta_e76(lab1: tuple[Decimal, Decimal, Decimal], lab2: tuple[Decimal, Decimal, Decimal]) -> Decimal:
    """Distancia euclidiana CIE76 entre dos puntos Lab. Suficiente para detectar
    qué tan lejos estás del objetivo; no corrige percepción como CIEDE2000."""
    diffs_cuadrado = [(float(x) - float(y)) ** 2 for x, y in zip(lab1, lab2)]
    distancia = math.sqrt(sum(diffs_cuadrado))
    return Decimal(str(distancia)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_ajuste_componente(
    lab_target: tuple[Decimal, Decimal, Decimal],
    lab_before: tuple[Decimal, Decimal, Decimal],
    lab_after: tuple[Decimal, Decimal, Decimal],
    grams_added: Decimal,
) -> list[dict]:
    """
    Para cada eje (L, a, b): calcula cuánto se movió por gramo agregado
    (sensibilidad) y cuántos gramos más harían falta para llegar al objetivo,
    asumiendo que la relación gramos->movimiento sigue siendo lineal cerca
    de este punto (válido para dosis de ajuste pequeñas, como en tu proceso).
    """
    resultado = []
    for i, eje in enumerate(EJES):
        antes, despues, objetivo = lab_before[i], lab_after[i], lab_target[i]
        sensibilidad = (despues - antes) / grams_added
        delta_restante = objetivo - despues

        if sensibilidad == 0:
            grs_sugeridos = None
            overshoot = False
        else:
            grs_sugeridos = (delta_restante / sensibilidad).quantize(
                Decimal("0.001"), rounding=ROUND_HALF_UP
            )
            overshoot = grs_sugeridos < 0

        resultado.append(
            {
                "eje": eje,
                "sensibilidad_por_gramo": sensibilidad.quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                ),
                "delta_restante": delta_restante,
                "grs_sugeridos": grs_sugeridos,
                "overshoot": overshoot,
            }
        )
    return resultado