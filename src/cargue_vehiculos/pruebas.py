"""Pruebas de la operación 3 (cargue de vehículos).

Se ejecutan con ``python src/cargue_vehiculos/pruebas.py`` desde la raíz
del repositorio. Si todo está bien, el script termina imprimiendo un
mensaje; si algo falla, se detiene en el ``assert`` que no se cumple.
"""

from datos import generar_dia, generar_lotes, generar_lotes_pequenos
from estrategia import Lote, cargar_vehiculo
from exhaustivo import cargar_exhaustivo
from regla_actual import cargar_por_densidad, cargar_por_vencimiento

# Ejemplo resuelto a mano en el informe: 5 lotes, capacidad de 10 kg.
# (peso_kg, valor_nutricional, dias_para_vencer)
EJEMPLO: list[Lote] = [
    (6, 30, 1),
    (5, 50, 2),
    (5, 50, 3),
    (6, 66, 4),
    (3, 14, 5),
]
CAPACIDAD_EJEMPLO = 10


def peso_de(lotes: list[Lote], indices: list[int]) -> int:
    """Suma el peso de los lotes indicados.

    Args:
        lotes: lotes candidatos.
        indices: índices de los lotes elegidos.

    Returns:
        El peso total en kilogramos.
    """
    return sum(lotes[i][0] for i in indices)


def valor_de(lotes: list[Lote], indices: list[int]) -> int:
    """Suma el valor nutricional de los lotes indicados.

    Args:
        lotes: lotes candidatos.
        indices: índices de los lotes elegidos.

    Returns:
        El valor nutricional total.
    """
    return sum(lotes[i][1] for i in indices)


def probar_casos_limite() -> None:
    """Revisa entrada vacía, un lote, nada cabe, todo cabe y errores."""
    assert cargar_vehiculo([], 100) == (0, [])
    assert cargar_vehiculo([(10, 5, 3)], 10) == (5, [0])
    assert cargar_vehiculo([(10, 5, 3)], 9) == (0, [])
    assert cargar_vehiculo([(10, 5, 3), (20, 8, 2)], 0) == (0, [])
    # Nada cabe.
    assert cargar_vehiculo([(50, 9, 1), (60, 7, 2)], 40) == (0, [])
    # Todo cabe.
    assert cargar_vehiculo([(5, 3, 1), (6, 4, 2)], 100) == (7, [0, 1])
    # El peso exacto de la capacidad sí se puede cargar.
    assert cargar_vehiculo([(4, 10, 1), (6, 12, 2)], 10) == (22, [0, 1])
    for funcion in (cargar_exhaustivo, cargar_por_vencimiento):
        assert funcion([], 100) == (0, [])
    # Capacidad negativa y lote vencido (días para vencer < 0) se rechazan.
    for lotes, capacidad in (([(1, 1, 1)], -1), ([(1, 1, -1)], 10)):
        for funcion in (cargar_vehiculo, cargar_por_vencimiento,
                        cargar_por_densidad, cargar_exhaustivo):
            try:
                funcion(lotes, capacidad)
            except ValueError:
                continue
            raise AssertionError("Debía rechazar la entrada inválida.")


def probar_ejemplo_a_mano() -> None:
    """Revisa el ejemplo del informe, calculado a mano."""
    assert cargar_vehiculo(EJEMPLO, CAPACIDAD_EJEMPLO) == (100, [1, 2])
    assert cargar_exhaustivo(EJEMPLO, CAPACIDAD_EJEMPLO) == (100, [1, 2])


def probar_contra_exhaustivo() -> None:
    """Compara la estrategia con la exhaustiva en 25 instancias pequeñas."""
    for semilla in range(25):
        n = 1 + semilla % 14
        lotes = generar_lotes_pequenos(n, semilla)
        capacidad = max(1, peso_de(lotes, list(range(n))) // 3)
        optimo, _ = cargar_exhaustivo(lotes, capacidad)
        valor, elegidos = cargar_vehiculo(lotes, capacidad)
        assert valor == optimo, (semilla, valor, optimo)
        assert valor_de(lotes, elegidos) == valor
        assert peso_de(lotes, elegidos) <= capacidad


def probar_restricciones_del_negocio() -> None:
    """Ningún vehículo supera su capacidad y ningún lote se fracciona."""
    for lotes, capacidad in generar_dia(7)[:4]:
        valor, elegidos = cargar_vehiculo(lotes, capacidad)
        assert peso_de(lotes, elegidos) <= capacidad
        assert len(set(elegidos)) == len(elegidos)  # cada lote va entero
        assert all(0 <= i < len(lotes) for i in elegidos)
        assert valor_de(lotes, elegidos) == valor
        for regla in (cargar_por_vencimiento, cargar_por_densidad):
            valor_regla, por_regla = regla(lotes, capacidad)
            assert peso_de(lotes, por_regla) <= capacidad
            assert valor_regla <= valor


def probar_regla_actual_peor() -> None:
    """Usa el contraejemplo del informe: las dos reglas quedan por debajo."""
    optimo, _ = cargar_vehiculo(EJEMPLO, CAPACIDAD_EJEMPLO)
    por_vencimiento = cargar_por_vencimiento(EJEMPLO, CAPACIDAD_EJEMPLO)
    por_densidad = cargar_por_densidad(EJEMPLO, CAPACIDAD_EJEMPLO)
    assert por_vencimiento == (30, [0])
    assert por_densidad == (80, [3, 4])
    assert optimo - por_vencimiento[0] == 70
    assert optimo - por_densidad[0] == 20


def probar_reglas_nunca_superan_optimo() -> None:
    """En 25 instancias aleatorias ninguna regla supera a la estrategia."""
    for semilla in range(25):
        n = 5 + semilla % 20
        lotes = generar_lotes(n, semilla)
        capacidad = 1000 + 100 * (semilla % 10)
        optimo, _ = cargar_vehiculo(lotes, capacidad)
        assert cargar_por_vencimiento(lotes, capacidad)[0] <= optimo
        assert cargar_por_densidad(lotes, capacidad)[0] <= optimo


def probar_datos_originales_intactos() -> None:
    """Ninguna solución modifica la lista de lotes que recibe."""
    lotes = generar_lotes(200, 5)
    copia = list(lotes)
    for funcion in (cargar_vehiculo, cargar_por_vencimiento,
                    cargar_por_densidad):
        funcion(lotes, 3000)
        assert lotes == copia
    pequenos = generar_lotes_pequenos(10, 5)
    copia = list(pequenos)
    cargar_exhaustivo(pequenos, 40)
    assert pequenos == copia


def probar_contador() -> None:
    """La estrategia calcula exactamente n * (W + 1) celdas."""
    lotes = generar_lotes_pequenos(12, 3)
    contador = [0]
    cargar_vehiculo(lotes, 50, contador)
    assert contador[0] == 12 * 51
    contador = [0]
    cargar_exhaustivo(lotes[:6], 30, contador)
    assert contador[0] == 6 * 2**6


if __name__ == "__main__":
    probar_casos_limite()
    probar_ejemplo_a_mano()
    probar_contra_exhaustivo()
    probar_restricciones_del_negocio()
    probar_regla_actual_peor()
    probar_reglas_nunca_superan_optimo()
    probar_datos_originales_intactos()
    probar_contador()
    print("Operación 3: todas las pruebas pasaron.")
