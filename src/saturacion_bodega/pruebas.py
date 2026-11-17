"""Pruebas de la operación 4 (saturación de la bodega).

Se ejecutan con ``python src/saturacion_bodega/pruebas.py`` desde la raíz
del repositorio.
"""

from datos import generar_serie, generar_serie_pequena
from estrategia import tramo_maximo_dyv, tramo_maximo_kadane
from exhaustivo import tramo_maximo_exhaustivo
from regla_actual import tramo_maximo_actual

SOLUCIONES = (
    tramo_maximo_dyv,
    tramo_maximo_kadane,
    tramo_maximo_actual,
    tramo_maximo_exhaustivo,
)

# Ejemplo clásico de 16 horas (Cormen et al., sección 4.1).
EJEMPLO = [13, -3, -25, 20, -3, -16, -23, 18, 20, -7, 12, -5, -22, 15, -4, 7]


def probar_casos_limite() -> None:
    """Revisa un solo elemento, todo negativo, todo positivo y vacío."""
    for solucion in SOLUCIONES:
        assert solucion([5]) == (5, 0, 0)
        assert solucion([-5]) == (-5, 0, 0)
        assert solucion([-3, -1, -2])[0] == -1  # el menos malo
        assert solucion([4, 2, 7]) == (13, 0, 2)
        assert solucion([0, 0, 0])[0] == 0
        try:
            solucion([])
        except ValueError:
            continue
        raise AssertionError("Debía fallar con la serie vacía.")


def probar_ejemplo_a_mano() -> None:
    """Revisa el ejemplo del informe: el mejor tramo suma 43 (horas 7 a 10)."""
    for solucion in SOLUCIONES:
        assert solucion(EJEMPLO) == (43, 7, 10)


def suma_del_tramo(serie: list[int], tramo: tuple[int, int, int]) -> int:
    """Suma las horas del tramo indicado.

    Args:
        serie: cambio neto del inventario por hora.
        tramo: suma, hora inicial y hora final del tramo.

    Returns:
        La suma real de las horas entre la inicial y la final.
    """
    _, inicio, fin = tramo
    return sum(serie[inicio:fin + 1])


def probar_contra_exhaustivo() -> None:
    """Las cuatro soluciones coinciden en 25 series aleatorias pequeñas."""
    for semilla in range(25):
        serie = generar_serie_pequena(1 + semilla * 2, semilla)
        esperado = tramo_maximo_exhaustivo(serie)[0]
        for solucion in SOLUCIONES:
            tramo = solucion(serie)
            assert tramo[0] == esperado, (solucion.__name__, semilla)
            assert suma_del_tramo(serie, tramo) == tramo[0]


def probar_series_medianas() -> None:
    """Las soluciones rápidas coinciden con la actual en series de 600 h."""
    for semilla in range(10):
        serie = generar_serie(600, semilla)
        esperado = tramo_maximo_actual(serie)[0]
        for solucion in (tramo_maximo_dyv, tramo_maximo_kadane):
            tramo = solucion(serie)
            assert tramo[0] == esperado
            assert suma_del_tramo(serie, tramo) == tramo[0]


def probar_serie_original_intacta() -> None:
    """Ninguna solución modifica la serie que recibe."""
    serie = generar_serie(300, 4)
    copia = list(serie)
    for solucion in SOLUCIONES:
        solucion(serie)
        assert serie == copia


def probar_contador() -> None:
    """Revisa los conteos exactos de la solución actual y de Kadane."""
    serie = generar_serie_pequena(40, 1)
    contador = [0]
    tramo_maximo_actual(serie, contador)
    assert contador[0] == 40 * 41 // 2
    contador = [0]
    tramo_maximo_kadane(serie, contador)
    assert contador[0] == 40


if __name__ == "__main__":
    probar_casos_limite()
    probar_ejemplo_a_mano()
    probar_contra_exhaustivo()
    probar_series_medianas()
    probar_serie_original_intacta()
    probar_contador()
    print("Operación 4: todas las pruebas pasaron.")
