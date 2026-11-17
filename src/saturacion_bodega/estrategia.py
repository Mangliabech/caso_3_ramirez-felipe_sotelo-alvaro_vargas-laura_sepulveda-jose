"""Tramo de mayor crecimiento del inventario de una categoría.

Dada la serie de cambios netos por hora (en kg, pueden ser negativos), se
busca el tramo de horas consecutivas con mayor suma. Aquí están las dos
estrategias propuestas: divide y vencerás y programación dinámica
(algoritmo de Kadane).
"""

# (suma_maxima_kg, hora_inicial, hora_final); las horas son índices
# de la serie y el tramo incluye ambos extremos.
Tramo = tuple[int, int, int]


def validar_serie(serie: list[int]) -> None:
    """Revisa que la serie tenga al menos una hora.

    Args:
        serie: cambio neto del inventario por hora, en kilogramos.

    Raises:
        ValueError: si la serie está vacía.
    """
    if not serie:
        raise ValueError("La serie debe tener al menos una hora.")


def tramo_maximo_dyv(
    serie: list[int], contador: list[int] | None = None
) -> Tramo:
    """Encuentra el tramo de mayor suma dividiendo la serie por la mitad.

    El mejor tramo está completo en la mitad izquierda, completo en la
    derecha, o cruza el punto medio. Los dos primeros casos se resuelven
    con la misma función; el tercero se resuelve recorriendo hacia afuera
    desde el punto medio.

    Args:
        serie: cambio neto del inventario por hora, en kilogramos.
        contador: lista de un elemento donde se suman las operaciones
            elementales (sumas y comparaciones del recorrido). Es opcional
            y solo sirve para las mediciones.

    Returns:
        La suma máxima y las horas inicial y final del tramo.

    Raises:
        ValueError: si la serie está vacía.
    """
    validar_serie(serie)
    return _dyv(serie, 0, len(serie) - 1, contador)


def _dyv(
    serie: list[int], bajo: int, alto: int, contador: list[int] | None
) -> Tramo:
    """Resuelve el subproblema de la serie entre ``bajo`` y ``alto``.

    Args:
        serie: cambio neto del inventario por hora, en kilogramos.
        bajo: primer índice del subproblema.
        alto: último índice del subproblema (incluido).
        contador: contador opcional de operaciones elementales.

    Returns:
        La suma máxima y las horas inicial y final del mejor tramo.
    """
    if bajo == alto:
        if contador is not None:
            contador[0] += 1
        return serie[bajo], bajo, bajo
    medio = (bajo + alto) // 2
    izquierda = _dyv(serie, bajo, medio, contador)
    derecha = _dyv(serie, medio + 1, alto, contador)
    cruce = _tramo_cruzado(serie, bajo, medio, alto, contador)
    return max(izquierda, derecha, cruce, key=lambda tramo: tramo[0])


def _tramo_cruzado(
    serie: list[int],
    bajo: int,
    medio: int,
    alto: int,
    contador: list[int] | None,
) -> Tramo:
    """Busca el mejor tramo que contiene a ``medio`` y a ``medio + 1``.

    Args:
        serie: cambio neto del inventario por hora, en kilogramos.
        bajo: primer índice del subproblema.
        medio: último índice de la mitad izquierda.
        alto: último índice del subproblema (incluido).
        contador: contador opcional de operaciones elementales.

    Returns:
        La suma máxima y las horas inicial y final del mejor tramo cruzado.
    """
    suma = 0
    mejor_izquierda = serie[medio]
    inicio = medio
    for i in range(medio, bajo - 1, -1):
        suma += serie[i]
        if suma > mejor_izquierda or i == medio:
            mejor_izquierda = suma
            inicio = i
    suma = 0
    mejor_derecha = serie[medio + 1]
    fin = medio + 1
    for j in range(medio + 1, alto + 1):
        suma += serie[j]
        if suma > mejor_derecha or j == medio + 1:
            mejor_derecha = suma
            fin = j
    if contador is not None:
        contador[0] += alto - bajo + 1
    return mejor_izquierda + mejor_derecha, inicio, fin


def tramo_maximo_kadane(
    serie: list[int], contador: list[int] | None = None
) -> Tramo:
    """Encuentra el tramo de mayor suma con programación dinámica.

    Sea ``terminando[j]`` la mejor suma de un tramo que termina justo en la
    hora ``j``. Entonces
    ``terminando[j] = max(serie[j], terminando[j-1] + serie[j])``,
    y la respuesta es el mayor ``terminando[j]``. Como solo se necesita el
    valor anterior, no se guarda todo el arreglo.

    Args:
        serie: cambio neto del inventario por hora, en kilogramos.
        contador: lista de un elemento donde se suman los pasos hechos (uno
            por hora). Es opcional y solo sirve para las mediciones.

    Returns:
        La suma máxima y las horas inicial y final del tramo.

    Raises:
        ValueError: si la serie está vacía.
    """
    validar_serie(serie)
    mejor = serie[0]
    mejor_inicio = mejor_fin = 0
    actual = serie[0]
    inicio_actual = 0
    for j in range(1, len(serie)):
        if actual < 0:  # arrastrar lo anterior solo restaría
            actual = serie[j]
            inicio_actual = j
        else:
            actual += serie[j]
        if actual > mejor:
            mejor = actual
            mejor_inicio, mejor_fin = inicio_actual, j
    if contador is not None:
        contador[0] += len(serie)
    return mejor, mejor_inicio, mejor_fin
