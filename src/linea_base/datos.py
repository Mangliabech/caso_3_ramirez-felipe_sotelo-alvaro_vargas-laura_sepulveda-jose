"""Generador de inventarios sintéticos para la línea base."""

import random

from procesos_actuales import LoteInventario


def generar_inventario(n: int, semilla: int) -> list[LoteInventario]:
    """Genera n lotes con código único, categoría y fecha de vencimiento.

    Args:
        n: número de lotes.
        semilla: semilla del generador aleatorio.

    Returns:
        Lista de (codigo_lote, categoria, fecha_vencimiento) sin ordenar.
    """
    rng = random.Random(semilla)
    codigos = rng.sample(range(10 * n), n)
    return [(c, rng.randint(1, 40), rng.randint(1, 365)) for c in codigos]


def generar_ordenado_con_nuevos(
    n: int, nuevos: int, semilla: int
) -> list[LoteInventario]:
    """Genera la situación de la operación 2: lista ordenada más lotes nuevos.

    Args:
        n: lotes del día anterior (ya ordenados).
        nuevos: lotes del día que se anexan al final sin orden.
        semilla: semilla del generador aleatorio.

    Returns:
        Los n lotes ordenados seguidos de los lotes nuevos.
    """
    todos = generar_inventario(n + nuevos, semilla)
    viejos = sorted(todos[:n], key=lambda lote: (lote[2], lote[1]))
    return viejos + todos[n:]
