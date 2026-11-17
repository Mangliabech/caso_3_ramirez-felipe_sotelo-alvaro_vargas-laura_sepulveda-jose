"""Pruebas de la línea base (operaciones 1 y 2 actuales).

Se ejecutan con ``python src/linea_base/pruebas.py`` desde la raíz.
"""

from datos import generar_inventario, generar_ordenado_con_nuevos
from procesos_actuales import (
    buscar_lote_lista,
    lotes_en_rango_lista,
    ordenar_por_insercion,
)


def probar_busqueda_y_rango() -> None:
    """Revisa la búsqueda por código y la consulta por rango."""
    inventario = generar_inventario(500, 1)
    assert buscar_lote_lista([], 5) is None
    for lote in inventario[:20]:
        assert buscar_lote_lista(inventario, lote[0]) == lote
    assert buscar_lote_lista(inventario, -1) is None
    rango = lotes_en_rango_lista(inventario, 10, 20)
    assert all(10 <= lote[2] <= 20 for lote in rango)
    assert len(rango) == sum(1 for lote in inventario if 10 <= lote[2] <= 20)


def probar_ordenamiento() -> None:
    """Revisa que la inserción ordene bien y no toque la lista original."""
    assert ordenar_por_insercion([]) == []
    lotes = generar_ordenado_con_nuevos(300, 30, 2)
    copia = list(lotes)
    ordenado = ordenar_por_insercion(lotes)
    assert lotes == copia
    esperado = sorted(lotes, key=lambda lote: (lote[2], lote[1]))
    claves = [(lote[2], lote[1]) for lote in ordenado]
    assert claves == [(lote[2], lote[1]) for lote in esperado]
    assert sorted(ordenado) == sorted(lotes)  # no se pierde ningún lote


if __name__ == "__main__":
    probar_busqueda_y_rango()
    probar_ordenamiento()
    print("Línea base: todas las pruebas pasaron.")
