"""Solución exhaustiva del tramo máximo: suma cada tramo desde cero.

Su costo es cúbico, así que solo se usa con series cortas para comprobar
que las otras soluciones dan la misma suma máxima.
"""

from estrategia import Tramo, validar_serie


def tramo_maximo_exhaustivo(
    serie: list[int], contador: list[int] | None = None
) -> Tramo:
    """Prueba todos los tramos y vuelve a sumar sus horas cada vez.

    Args:
        serie: cambio neto del inventario por hora, en kilogramos.
        contador: lista de un elemento donde se suman las horas sumadas.
            Es opcional y solo sirve para las mediciones.

    Returns:
        La suma máxima y las horas inicial y final del tramo; si hay
        empate se queda con el primero que encuentra.

    Raises:
        ValueError: si la serie está vacía.
    """
    validar_serie(serie)
    n = len(serie)
    mejor = serie[0]
    mejor_inicio = mejor_fin = 0
    for i in range(n):
        for j in range(i, n):
            suma = sum(serie[i:j + 1])
            if contador is not None:
                contador[0] += j - i + 1
            if suma > mejor:
                mejor = suma
                mejor_inicio, mejor_fin = i, j
    return mejor, mejor_inicio, mejor_fin
