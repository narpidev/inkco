from decimal import ROUND_HALF_UP, Decimal


def calcular_gramos_por_porcentaje(
    total_grs: Decimal, componentes: list[tuple[str, Decimal]]
) -> list[dict]:
    """
    Dado un total a preparar y una lista de (nombre, porcentaje),
    devuelve cuántos gramos corresponden a cada componente.

    No exige que los porcentajes sumen exactamente 100: si suman menos o más,
    el resultado sigue siendo proporcional (total_grs * porcentaje / 100).
    """
    resultado = []
    for nombre, porcentaje in componentes:
        grs = (total_grs * porcentaje / Decimal("100")).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )
        resultado.append({"component_name": nombre, "percentage": porcentaje, "grs": grs})
    return resultado

def calcular_porcentaje_por_gramos(
    total_grs: Decimal, componentes: list[tuple[str, Decimal]]
) -> list[dict]:
    """
    Dado un total y una lista de (nombre, grs), devuelve el % que
    representa cada componente sobre el total.
    """
    resultado = []
    for nombre, grs in componentes:
        porcentaje = (grs / total_grs * Decimal("100")).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )
        resultado.append({"component_name": nombre, "grs": grs, "percentage": porcentaje})
    return resultado