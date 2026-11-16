"""Cargue de un vehículo del banco de alimentos con programación dinámica.

Es el problema de la mochila 0/1: cada lote sube completo o no sube, el
peso total no puede superar la capacidad y se busca el máximo valor
nutricional.
"""

# (peso_kg, valor_nutricional, dias_para_vencer)
Lote = tuple[int, int, int]


def validar_entrada(lotes: list[Lote], capacidad_kg: int) -> None:
    """Revisa que los lotes y la capacidad cumplan lo que asume el problema.

    Args:
        lotes: lotes candidatos de la ruta.
        capacidad_kg: capacidad máxima del vehículo en kilogramos.

    Raises:
        ValueError: si la capacidad es negativa, si algún lote tiene peso
            menor que 1 o valor negativo, o si algún lote ya está vencido
            (días para vencer negativos): un lote vencido nunca se despacha.
    """
    if capacidad_kg < 0:
        raise ValueError("La capacidad no puede ser negativa.")
    for peso, valor, dias in lotes:
        if peso < 1 or valor < 0:
            raise ValueError("Cada lote necesita peso >= 1 y valor >= 0.")
        if dias < 0:
            raise ValueError("No se puede cargar un lote vencido.")


def cargar_vehiculo(
    lotes: list[Lote],
    capacidad_kg: int,
    contador: list[int] | None = None,
) -> tuple[int, list[int]]:
    """Elige los lotes de mayor valor nutricional que caben en el vehículo.

    Usa una tabla ``tabla[i][w]`` con el valor máximo que se puede cargar
    con los primeros ``i`` lotes y una capacidad de ``w`` kg:

    ``tabla[i][w] = max(tabla[i-1][w], tabla[i-1][w-peso_i] + valor_i)``

    (la segunda opción solo existe si ``peso_i <= w``). Después se recorre
    la tabla hacia atrás para saber qué lotes se cargaron.

    Args:
        lotes: lotes candidatos de la ruta; no se fraccionan.
        capacidad_kg: capacidad máxima del vehículo en kilogramos.
        contador: lista de un elemento donde se suma el número de celdas
            calculadas. Es opcional y solo sirve para las mediciones.

    Returns:
        El valor nutricional máximo y los índices de los lotes cargados,
        en orden creciente.
    """
    validar_entrada(lotes, capacidad_kg)
    n = len(lotes)
    tabla = [[0] * (capacidad_kg + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        peso, valor, _ = lotes[i - 1]
        anterior = tabla[i - 1]
        actual = tabla[i]
        for w in range(capacidad_kg + 1):
            mejor = anterior[w]
            if peso <= w:
                con_lote = anterior[w - peso] + valor
                if con_lote > mejor:
                    mejor = con_lote
            actual[w] = mejor
        if contador is not None:
            contador[0] += capacidad_kg + 1
    return tabla[n][capacidad_kg], reconstruir(lotes, tabla, capacidad_kg)


def reconstruir(
    lotes: list[Lote], tabla: list[list[int]], capacidad_kg: int
) -> list[int]:
    """Recorre la tabla hacia atrás para saber qué lotes se cargaron.

    Si ``tabla[i][w]`` es distinto de ``tabla[i-1][w]``, el lote ``i``
    tuvo que subir, y se sigue buscando con la capacidad que queda.

    Args:
        lotes: lotes candidatos de la ruta.
        tabla: tabla de programación dinámica ya calculada.
        capacidad_kg: capacidad máxima del vehículo en kilogramos.

    Returns:
        Los índices de los lotes cargados, en orden creciente.
    """
    elegidos: list[int] = []
    w = capacidad_kg
    for i in range(len(lotes), 0, -1):
        if tabla[i][w] != tabla[i - 1][w]:
            elegidos.append(i - 1)
            w -= lotes[i - 1][0]
    elegidos.reverse()
    return elegidos
