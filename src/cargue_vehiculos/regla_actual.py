"""Reglas de cargue que se usan o se podrían usar hoy en el banco.

Ninguna de las dos garantiza el valor nutricional máximo.
"""

from collections.abc import Callable
from functools import cmp_to_key

from estrategia import Lote, validar_entrada


def ordenar_indices(
    n: int,
    comparar: Callable[[int, int], int],
    contador: list[int] | None = None,
) -> list[int]:
    """Ordena los índices de 0 a n-1 con una función de comparación.

    El ordenamiento de Python es estable, así que los empates conservan el
    orden original de los lotes. Si se pasa un contador, se cuentan las
    comparaciones que hace el ordenamiento.

    Args:
        n: cantidad de lotes.
        comparar: función que recibe dos índices y devuelve un número
            negativo, cero o positivo.
        contador: lista de un elemento donde se suman las comparaciones.
            Es opcional y solo sirve para las mediciones.

    Returns:
        Los índices ordenados.
    """
    if contador is None:
        return sorted(range(n), key=cmp_to_key(comparar))

    def comparar_contando(a: int, b: int) -> int:
        """Compara dos índices y suma una comparación al contador."""
        contador[0] += 1
        return comparar(a, b)

    return sorted(range(n), key=cmp_to_key(comparar_contando))


def cargar_por_vencimiento(
    lotes: list[Lote],
    capacidad_kg: int,
    contador: list[int] | None = None,
) -> tuple[int, list[int]]:
    """Reproduce el procedimiento actual: carga por vencimiento.

    Se ordenan los lotes por días para vencer (primero el que vence antes)
    y se cargan en ese orden. Se detiene en el primer lote que ya no cabe,
    aunque más adelante haya lotes pequeños que sí cabrían.

    Args:
        lotes: lotes candidatos de la ruta.
        capacidad_kg: capacidad máxima del vehículo en kilogramos.
        contador: lista de un elemento donde se suman las comparaciones del
            ordenamiento y los lotes revisados. Es opcional y solo sirve
            para las mediciones.

    Returns:
        El valor nutricional cargado y los índices de los lotes cargados,
        en orden creciente.
    """
    validar_entrada(lotes, capacidad_kg)
    orden = ordenar_indices(
        len(lotes), lambda a, b: lotes[a][2] - lotes[b][2], contador
    )
    restante = capacidad_kg
    valor_total = 0
    elegidos: list[int] = []
    for i in orden:
        if contador is not None:
            contador[0] += 1
        peso, valor, _ = lotes[i]
        if peso > restante:
            break
        restante -= peso
        valor_total += valor
        elegidos.append(i)
    return valor_total, sorted(elegidos)


def cargar_por_densidad(
    lotes: list[Lote],
    capacidad_kg: int,
    contador: list[int] | None = None,
) -> tuple[int, list[int]]:
    """Carga por mayor valor por kilogramo; no garantiza el óptimo.

    Se ordenan los lotes por densidad (valor entre peso) de mayor a menor
    y se agrega cada lote que quepa, sin fraccionar. A diferencia de la
    regla de vencimiento, aquí no se detiene en el primer lote que no cabe:
    sigue buscando entre los siguientes.

    Args:
        lotes: lotes candidatos de la ruta.
        capacidad_kg: capacidad máxima del vehículo en kilogramos.
        contador: lista de un elemento donde se suman las comparaciones del
            ordenamiento y los lotes revisados. Es opcional y solo sirve
            para las mediciones.

    Returns:
        El valor nutricional cargado y los índices de los lotes cargados,
        en orden creciente.
    """
    validar_entrada(lotes, capacidad_kg)

    def mayor_densidad_primero(a: int, b: int) -> int:
        """Compara dos lotes por densidad sin usar divisiones."""
        return lotes[b][1] * lotes[a][0] - lotes[a][1] * lotes[b][0]

    orden = ordenar_indices(len(lotes), mayor_densidad_primero, contador)
    restante = capacidad_kg
    valor_total = 0
    elegidos: list[int] = []
    for i in orden:
        if contador is not None:
            contador[0] += 1
        peso, valor, _ = lotes[i]
        if peso <= restante:
            restante -= peso
            valor_total += valor
            elegidos.append(i)
    return valor_total, sorted(elegidos)
