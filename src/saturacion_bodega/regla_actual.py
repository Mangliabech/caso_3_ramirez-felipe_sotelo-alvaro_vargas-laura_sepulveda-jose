"""Procedimiento actual de la Dirección: evaluar todos los tramos.

El programa de hoy mira cada pareja (hora inicial, hora final). Aquí se
implementa llevando la suma acumulada del tramo, lo que da un costo
cuadrático.
"""

from estrategia import Tramo, validar_serie


def tramo_maximo_actual(
    serie: list[int], contador: list[int] | None = None
) -> Tramo:
    """Evalúa todos los tramos posibles reutilizando la suma anterior.

    Args:
        serie: cambio neto del inventario por hora, en kilogramos.
        contador: lista de un elemento donde se suman los tramos evaluados.
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
        suma = 0
        for j in range(i, n):
            suma += serie[j]
            if suma > mejor:
                mejor = suma
                mejor_inicio, mejor_fin = i, j
        if contador is not None:
            contador[0] += n - i
    return mejor, mejor_inicio, mejor_fin
