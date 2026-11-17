"""Mediciones y gráficas de la operación 4 (saturación de la bodega).

Se ejecuta con ``python src/saturacion_bodega/medicion.py`` desde la raíz
del repositorio. Genera las gráficas en ``graficas/saturacion_bodega/`` y
los números del informe en ``resultados/saturacion_bodega.json``.
"""

import json
import statistics
import time
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from datos import generar_serie  # noqa: E402
from estrategia import (  # noqa: E402
    Tramo,
    tramo_maximo_dyv,
    tramo_maximo_kadane,
)
from exhaustivo import tramo_maximo_exhaustivo  # noqa: E402
from regla_actual import tramo_maximo_actual  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
CARPETA_GRAFICAS = RAIZ / "graficas" / "saturacion_bodega"
ARCHIVO_RESULTADOS = RAIZ / "resultados" / "saturacion_bodega.json"

SEMILLA = 2026
TAMANOS_EXHAUSTIVO = [16, 32, 64, 128, 256, 512, 1024]
TAMANOS_ACTUAL = TAMANOS_EXHAUSTIVO + [2048, 4096, 8192, 16384]
TAMANOS_RAPIDAS = TAMANOS_ACTUAL + [
    32768, 36000, 65536, 131072, 262144, 524288,
]

HORAS_REALES = 36000  # diez años: 300 días * 12 horas * 10 años
CATEGORIAS = 40
VENTANA_S = 2 * 3600  # referencia: la ventana de planeación de 2 horas
POTENCIA_KW = 0.150
CORRIDAS_POR_ANIO = 12  # supuesto: un análisis mensual de temporada
DIAS_CLIENTE_S = 24 * 3600  # el cliente dice que tarda "más de un día"

Solucion = Callable[[list[int], list[int] | None], Tramo]


def medir(funcion: Callable[[], object], repeticiones: int = 3) -> float:
    """Mide el tiempo medio de una ejecución con ``time.perf_counter``.

    Si la primera ejecución tarda más de 2 segundos no se repite.

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


def experimento_tamano() -> dict[str, dict[int, dict[str, float]]]:
    """Mide tiempo y operaciones de cada solución contra el tamaño de serie.

    Returns:
        Para cada solución, los resultados por tamaño.
    """
    soluciones: dict[str, tuple[Solucion, list[int]]] = {
        "exhaustivo": (tramo_maximo_exhaustivo, TAMANOS_EXHAUSTIVO),
        "actual": (tramo_maximo_actual, TAMANOS_ACTUAL),
        "dyv": (tramo_maximo_dyv, TAMANOS_RAPIDAS),
        "kadane": (tramo_maximo_kadane, TAMANOS_RAPIDAS),
    }
    resultados: dict[str, dict[int, dict[str, float]]] = {
        nombre: {} for nombre in soluciones
    }
    for n in TAMANOS_RAPIDAS:
        serie = generar_serie(n, SEMILLA + n)  # datos fuera del cronómetro
        sumas = set()
        for nombre, (funcion, tamanos) in soluciones.items():
            if n not in tamanos:
                continue
            tiempo = medir(lambda: funcion(serie, None))
            contador = [0]
            sumas.add(funcion(serie, contador)[0])
            resultados[nombre][n] = {
                "tiempo_s": tiempo,
                "operaciones": contador[0],
            }
        assert len(sumas) == 1, f"Las soluciones no coinciden en n = {n}"
        print(f"  n = {n} listo")
    return resultados


def proyectar(
    por_tamano: dict[str, dict[int, dict[str, float]]]
) -> dict[str, float]:
    """Proyecta tiempos y energía al histórico real de 40 categorías.

    La solución actual se extrapola con la ley cuadrática a partir de su
    mayor tamaño medido; las dos rápidas se midieron directamente con
    36.000 horas.

    Args:
        por_tamano: resultados del experimento contra el tamaño.

    Returns:
        Tiempos por categoría y totales, energía por corrida y por año.
    """
    n_max = max(TAMANOS_ACTUAL)
    t_max = por_tamano["actual"][n_max]["tiempo_s"]
    t_actual = t_max * (HORAS_REALES / n_max) ** 2
    t_dyv = por_tamano["dyv"][HORAS_REALES]["tiempo_s"]
    t_kadane = por_tamano["kadane"][HORAS_REALES]["tiempo_s"]
    resultado = {"n_maximo_actual_medido": n_max}
    for nombre, t in (("actual", t_actual), ("dyv", t_dyv),
                      ("kadane", t_kadane)):
        total = t * CATEGORIAS
        kwh = POTENCIA_KW * total / 3600
        resultado[f"t_categoria_{nombre}_s"] = t
        resultado[f"t_total_{nombre}_s"] = total
        resultado[f"fraccion_ventana_{nombre}"] = total / VENTANA_S
        resultado[f"kwh_corrida_{nombre}"] = kwh
        resultado[f"kwh_anio_{nombre}"] = kwh * CORRIDAS_POR_ANIO
    resultado["kwh_corrida_cliente"] = POTENCIA_KW * DIAS_CLIENTE_S / 3600
    resultado["kwh_anio_cliente"] = (
        resultado["kwh_corrida_cliente"] * CORRIDAS_POR_ANIO
    )
    resultado["kwh_anio_ahorro_actual_vs_kadane"] = (
        resultado["kwh_anio_actual"] - resultado["kwh_anio_kadane"]
    )
    return resultado


def graficar(por_tamano: dict[str, dict[int, dict[str, float]]]) -> None:
    """Guarda las dos gráficas de la operación.

    Args:
        por_tamano: resultados del experimento contra el tamaño.
    """
    CARPETA_GRAFICAS.mkdir(parents=True, exist_ok=True)
    etiquetas = {
        "exhaustivo": "Exhaustivo (suma cada tramo)",
        "actual": "Todos los tramos (procedimiento actual)",
        "dyv": "Divide y vencerás",
        "kadane": "Programación dinámica (Kadane)",
    }
    for llave, titulo, eje, archivo in (
        ("tiempo_s", "Tiempo para hallar el tramo de mayor saturación",
         "Tiempo medio (s)", "tiempo_vs_n.png"),
        ("operaciones", "Operaciones elementales según el tamaño de la serie",
         "Operaciones elementales", "operaciones_vs_n.png"),
    ):
        plt.figure(figsize=(8, 5))
        for nombre, datos in por_tamano.items():
            xs = sorted(datos)
            plt.plot(xs, [datos[x][llave] for x in xs], marker="o",
                     label=etiquetas[nombre])
        plt.xscale("log")
        plt.yscale("log")
        plt.title(titulo)
        plt.xlabel("Número de horas de la serie, n (horas)")
        plt.ylabel(eje)
        plt.grid(True, which="both", alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(CARPETA_GRAFICAS / archivo, dpi=130)
        plt.close()


def main() -> None:
    """Corre los experimentos, guarda gráficas y resultados."""
    print("Midiendo contra el tamaño de la serie...")
    por_tamano = experimento_tamano()
    proyeccion = proyectar(por_tamano)
    graficar(por_tamano)
    ARCHIVO_RESULTADOS.parent.mkdir(exist_ok=True)
    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as archivo:
        json.dump({"por_tamano": por_tamano, "proyeccion": proyeccion},
                  archivo, indent=2)
    print("Listo: gráficas y resultados guardados.")


if __name__ == "__main__":
    main()
