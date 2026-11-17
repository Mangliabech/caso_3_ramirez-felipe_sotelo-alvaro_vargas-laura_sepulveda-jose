"""Operaciones 1 y 2 tal como funcionan hoy en el banco (línea base).

No son propuestas del equipo: se implementan solo para medir cuánto cuestan
y poder compararlas con las operaciones 3 y 4, que sí tienen propuesta.
"""

# (codigo_lote, categoria, fecha_vencimiento); la fecha es un número de día.
LoteInventario = tuple[int, int, int]


def buscar_lote_lista(
    inventario: list[LoteInventario], codigo: int
) -> LoteInventario | None:
    """Busca un lote por código recorriendo la lista (operación 1).

    Args:
        inventario: lotes activos, sin orden particular.
        codigo: código del lote que se consulta.

    Returns:
        El lote encontrado, o None si no existe.
    """
    for lote in inventario:
        if lote[0] == codigo:
            return lote
    return None


def lotes_en_rango_lista(
    inventario: list[LoteInventario], desde: int, hasta: int
) -> list[LoteInventario]:
    """Devuelve los lotes que vencen en un rango, recorriendo la lista.

    Args:
        inventario: lotes activos, sin orden particular.
        desde: primera fecha del rango (incluida).
        hasta: última fecha del rango (incluida).

    Returns:
        Los lotes cuya fecha de vencimiento está en el rango.
    """
    encontrados = []
    for lote in inventario:
        if desde <= lote[2] <= hasta:
            encontrados.append(lote)
    return encontrados


def ordenar_por_insercion(lotes: list[LoteInventario]) -> list[LoteInventario]:
    """Ordena por fecha de vencimiento y categoría con inserción (op. 2).

    Se ordena una copia; la lista original no se modifica. Como la lista
    del día anterior ya viene ordenada, el trabajo está en los lotes nuevos
    del final, que hay que desplazar hacia su lugar.

    Args:
        lotes: lotes de la bodega; los nuevos van al final.

    Returns:
        Una lista nueva ordenada por (fecha_vencimiento, categoria).
    """
    resultado = list(lotes)
    for i in range(1, len(resultado)):
        actual = resultado[i]
        clave = (actual[2], actual[1])
        j = i - 1
        while j >= 0 and (resultado[j][2], resultado[j][1]) > clave:
            resultado[j + 1] = resultado[j]
            j -= 1
        resultado[j + 1] = actual
    return resultado
