"""Mide el costo de las cuatro operaciones críticas del proceso actual.

Se ejecuta con ``python src/linea_base/medicion.py`` desde la raíz del
repositorio, DESPUÉS de las mediciones de las operaciones 3 y 4, porque
reutiliza sus resultados (``resultados/*.json``). Genera
``graficas/linea_base/costo_por_operacion.png`` y
``resultados/linea_base.json``.
"""

import json
import random
import statistics
import time
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from datos import generar_inventario, generar_ordenado_con_nuevos  # noqa: E402
from procesos_actuales import (  # noqa: E402
    buscar_lote_lista,
    lotes_en_rango_lista,
    ordenar_por_insercion,
)

RAIZ = Path(__file__).resolve().parents[2]
CARPETA_GRAFICAS = RAIZ / "graficas" / "linea_base"
RESULTADOS = RAIZ / "resultados"

LOTES_ACTIVOS = 220_000
CONSULTAS_POR_DIA = 30_000
CONSULTAS_RANGO_POR_NOCHE = 40  # supuesto: una por categoría
LOTES_NUEVOS_POR_DIA = 7_500
TAMANOS_ORDENAMIENTO = [5_000, 10_000, 20_000, 40_000]
POTENCIA_KW = 0.150
DIAS_ANIO = 300
CORRIDAS_OP4_ANIO = 12  # supuesto: un análisis mensual
PLANEACION_CLIENTE_H = 4.5  # dato del cliente: operaciones 1 a 3
SEMILLA = 2026


def medir(funcion: Callable[[], object], repeticiones: int = 3) -> float:
    """Mide el tiempo medio de una ejecución con ``time.perf_counter``.

    Args:
        funcion: función sin argumentos que ejecuta lo que se quiere medir.
        repeticiones: número de ejecuciones que se promedian.

    Returns:
        El tiempo medio de una ejecución, en segundos.
    """
    tiempos = []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        funcion()
        tiempos.append(time.perf_counter() - inicio)
        if tiempos[0] > 2.0:
            break
    return statistics.mean(tiempos)


def medir_operacion_1() -> dict[str, float]:
    """Mide la consulta por código y por rango sobre 220.000 lotes.

    Returns:
        Tiempo medio de una consulta por código, de una por rango y total
        estimado de una noche (30.000 consultas y 40 consultas de rango).
    """
    inventario = generar_inventario(LOTES_ACTIVOS, SEMILLA)
    rng = random.Random(SEMILLA)
    codigos = [rng.choice(inventario)[0] for _ in range(100)]
    t_codigo = medir(
        lambda: [buscar_lote_lista(inventario, c) for c in codigos], 2
    ) / len(codigos)
    t_rango = medir(lambda: lotes_en_rango_lista(inventario, 100, 103))
    total = CONSULTAS_POR_DIA * t_codigo + CONSULTAS_RANGO_POR_NOCHE * t_rango
    return {"t_consulta_codigo_s": t_codigo, "t_consulta_rango_s": t_rango,
            "t_total_s": total}


def medir_operacion_2() -> dict[str, object]:
    """Mide el ordenamiento por inserción y lo proyecta a 227.500 lotes.

    Los lotes nuevos son el 3,4 % de la lista, como en el caso (7.500 de
    220.000). Se extrapola con la ley cuadrática desde el mayor tamaño.

    Returns:
        Los tiempos medidos por tamaño y el tiempo estimado del volumen real.
    """
    medidos = {}
    for n in TAMANOS_ORDENAMIENTO:
        nuevos = round(n * LOTES_NUEVOS_POR_DIA / LOTES_ACTIVOS)
        lotes = generar_ordenado_con_nuevos(n, nuevos, SEMILLA)
        medidos[n] = medir(lambda: ordenar_por_insercion(lotes))
        print(f"  ordenamiento n = {n} listo")
    n_max = max(TAMANOS_ORDENAMIENTO)
    estimado = medidos[n_max] * (LOTES_ACTIVOS / n_max) ** 2
    return {"medidos_s": medidos, "t_total_s": estimado}


def kwh(segundos: float) -> float:
    """Convierte segundos de ejecución en kWh con la potencia del equipo.

    Args:
        segundos: tiempo de ejecución en segundos.

    Returns:
        Energía consumida en kilovatios-hora.
    """
    return POTENCIA_KW * segundos / 3600


def graficar(tiempos: dict[str, float]) -> None:
    """Guarda la gráfica de tiempo estimado por operación.

    Args:
        tiempos: tiempo estimado, en segundos, de cada operación.
    """
    CARPETA_GRAFICAS.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    nombres = list(tiempos)
    plt.bar(nombres, [tiempos[n] for n in nombres], color="#3b7ea1")
    plt.yscale("log")
    plt.title("Tiempo estimado de cada operación con el volumen real")
    plt.xlabel("Operación del proceso actual")
    plt.ylabel("Tiempo estimado (s, escala logarítmica)")
    plt.xticks(rotation=12, fontsize=8)
    plt.grid(True, axis="y", which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(CARPETA_GRAFICAS / "costo_por_operacion.png", dpi=130)
    plt.close()


def main() -> None:
    """Mide las operaciones 1 y 2, junta las 3 y 4 y calcula la energía."""
    print("Midiendo operación 1...")
    op1 = medir_operacion_1()
    print("Midiendo operación 2...")
    op2 = medir_operacion_2()
    with open(RESULTADOS / "cargue_vehiculos.json", encoding="utf-8") as f:
        op3 = json.load(f)["dia_real"]
    with open(RESULTADOS / "saturacion_bodega.json", encoding="utf-8") as f:
        op4 = json.load(f)["proyeccion"]
    tiempos = {
        "1. Consulta de\ninventario": op1["t_total_s"],
        "2. Ordenamiento\nFEFO": op2["t_total_s"],
        "3. Cargue (regla\nactual)": op3["tiempo_regla_s"],
        "4. Saturación (todos\nlos tramos)": op4["t_total_actual_s"],
    }
    kwh_noche = {k: kwh(v) for k, v in tiempos.items()}
    planeacion = PLANEACION_CLIENTE_H * POTENCIA_KW
    resumen = {
        "operacion_1": op1,
        "operacion_2": op2,
        "tiempos_s": tiempos,
        "kwh_por_ejecucion": kwh_noche,
        "planeacion_cliente_kwh_noche": planeacion,
        "planeacion_cliente_kwh_anio": planeacion * DIAS_ANIO,
        "kwh_anio_op4_actual_medido": kwh(op4["t_total_actual_s"])
        * CORRIDAS_OP4_ANIO,
    }
    graficar(tiempos)
    with open(RESULTADOS / "linea_base.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    print("Listo: gráfica y resultados guardados.")


if __name__ == "__main__":
    main()
