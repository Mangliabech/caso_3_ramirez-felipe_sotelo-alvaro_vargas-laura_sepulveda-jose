"""Mediciones y gráficas de la operación 3 (cargue de vehículos).

Se ejecuta con ``python src/cargue_vehiculos/medicion.py`` desde la raíz
del repositorio. Genera las gráficas en ``graficas/cargue_vehiculos/`` y
los números del informe en ``resultados/cargue_vehiculos.json``.
"""

import json
import math
import statistics
import time
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from datos import generar_dia, generar_lotes  # noqa: E402
from estrategia import Lote, cargar_vehiculo  # noqa: E402
from exhaustivo import cargar_exhaustivo  # noqa: E402
from regla_actual import (  # noqa: E402
    cargar_por_densidad,
    cargar_por_vencimiento,
)

RAIZ = Path(__file__).resolve().parents[2]
CARPETA_GRAFICAS = RAIZ / "graficas" / "cargue_vehiculos"
ARCHIVO_RESULTADOS = RAIZ / "resultados" / "cargue_vehiculos.json"

SEMILLA = 2026
CAPACIDAD_FIJA = 3000  # kg, para la medición contra n
LOTES_FIJOS = 300  # lotes, para la medición contra W
TAMANOS_EXHAUSTIVO = [8, 10, 12, 14, 16, 18, 20, 22]
TAMANOS_ESTRATEGIA = TAMANOS_EXHAUSTIVO + [40, 80, 160, 320, 640, 1280, 2560]
CAPACIDADES = [500, 1000, 2000, 4000, 8000, 16000]
DIAS_SIMULADOS = 8

POTENCIA_KW = 0.150  # computador de la fundación: 150 W
DIAS_ANIO = 300  # el banco opera 300 días al año
VENTANA_S = 2 * 3600  # ventana de planeación compartida: 2 horas
CO2_POR_KG = 2.5  # kg CO2e por kg de alimento desechado (dato del banco)
CO2_POR_KWH = 0.112  # kg CO2 por kWh, factor de la UPME (año 2022)

Funcion = Callable[[list[Lote], int, list[int] | None], tuple[int, list[int]]]


def medir(funcion: Callable[[], object], repeticiones: int = 3) -> float:
    """Mide el tiempo medio de una ejecución con ``time.perf_counter``.

    Si la primera ejecución tarda más de 2 segundos no se repite, para que
    las mediciones grandes no se alarguen.

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


def contar(funcion: Funcion, lotes: list[Lote], capacidad: int) -> int:
    """Cuenta las operaciones elementales que hace una solución.

    Args:
        funcion: solución que acepta un contador opcional.
        lotes: lotes candidatos.
        capacidad: capacidad del vehículo en kilogramos.

    Returns:
        El número de operaciones elementales contadas.
    """
    contador = [0]
    funcion(lotes, capacidad, contador)
    return contador[0]


def experimento_tamano() -> dict[str, dict[int, dict[str, float]]]:
    """Mide tiempo y operaciones de cada solución contra el número de lotes.

    Returns:
        Un diccionario con, para cada solución, los resultados por tamaño.
    """
    soluciones: dict[str, tuple[Funcion, list[int]]] = {
        "estrategia": (cargar_vehiculo, TAMANOS_ESTRATEGIA),
        "exhaustivo": (cargar_exhaustivo, TAMANOS_EXHAUSTIVO),
        "vencimiento": (cargar_por_vencimiento, TAMANOS_ESTRATEGIA),
        "densidad": (cargar_por_densidad, TAMANOS_ESTRATEGIA),
    }
    resultados: dict[str, dict[int, dict[str, float]]] = {
        nombre: {} for nombre in soluciones
    }
    for n in TAMANOS_ESTRATEGIA:
        lotes = generar_lotes(n, SEMILLA + n)  # datos fuera del cronómetro
        for nombre, (funcion, tamanos) in soluciones.items():
            if n not in tamanos:
                continue
            tiempo = medir(lambda: funcion(lotes, CAPACIDAD_FIJA, None))
            operaciones = contar(funcion, lotes, CAPACIDAD_FIJA)
            resultados[nombre][n] = {
                "tiempo_s": tiempo,
                "operaciones": operaciones,
            }
        if n in TAMANOS_EXHAUSTIVO:  # verificación dentro del experimento
            optimo = cargar_exhaustivo(lotes, CAPACIDAD_FIJA)[0]
            assert cargar_vehiculo(lotes, CAPACIDAD_FIJA)[0] == optimo
        print(f"  n = {n} listo")
    return resultados


def experimento_capacidad() -> dict[int, dict[str, float]]:
    """Mide la estrategia con n fijo y la capacidad W creciente.

    Returns:
        Para cada capacidad, el tiempo y las celdas calculadas.
    """
    lotes = generar_lotes(LOTES_FIJOS, SEMILLA)
    resultados = {}
    for capacidad in CAPACIDADES:
        tiempo = medir(lambda: cargar_vehiculo(lotes, capacidad))
        celdas = contar(cargar_vehiculo, lotes, capacidad)
        resultados[capacidad] = {"tiempo_s": tiempo, "operaciones": celdas}
        print(f"  W = {capacidad} listo")
    return resultados


def experimento_calidad() -> dict[str, float]:
    """Compara llenado y valor de las tres soluciones en días simulados.

    Returns:
        Promedios de llenado (fracción de la capacidad) y de valor
        nutricional por vehículo, y los kilogramos extra diarios.
    """
    llenado: dict[str, list[float]] = {"vencimiento": [], "densidad": [],
                                       "estrategia": []}
    valores: dict[str, list[int]] = {k: [] for k in llenado}
    kg_extra_dia = []
    for semilla in range(1, DIAS_SIMULADOS + 1):
        extra = 0
        for lotes, capacidad in generar_dia(semilla):
            for nombre, funcion in (
                ("vencimiento", cargar_por_vencimiento),
                ("densidad", cargar_por_densidad),
                ("estrategia", cargar_vehiculo),
            ):
                valor, elegidos = funcion(lotes, capacidad)
                peso = sum(lotes[i][0] for i in elegidos)
                llenado[nombre].append(peso / capacidad)
                valores[nombre].append(valor)
                if nombre == "vencimiento":
                    extra -= peso
                elif nombre == "estrategia":
                    extra += peso
        kg_extra_dia.append(extra)
    resumen = {}
    for nombre in llenado:
        resumen[f"llenado_{nombre}"] = statistics.mean(llenado[nombre])
        resumen[f"valor_{nombre}"] = statistics.mean(valores[nombre])
    resumen["kg_extra_por_dia"] = statistics.mean(kg_extra_dia)
    return resumen


def experimento_dia_real() -> dict[str, float]:
    """Ejecuta un día completo con el volumen real (14 vehículos).

    Returns:
        Tiempo de la estrategia y de la regla actual para el día, y las
        celdas totales de la tabla de programación dinámica.
    """
    dia = generar_dia(99)
    celdas = sum(len(lotes) * (cap + 1) for lotes, cap in dia)
    t_estrategia = medir(
        lambda: [cargar_vehiculo(lotes, cap) for lotes, cap in dia], 1
    )
    t_regla = medir(
        lambda: [cargar_por_vencimiento(lotes, cap) for lotes, cap in dia]
    )
    return {"celdas": celdas, "tiempo_estrategia_s": t_estrategia,
            "tiempo_regla_s": t_regla}


def extrapolar(
    por_tamano: dict[str, dict[int, dict[str, float]]],
    dia_real: dict[str, float],
    calidad: dict[str, float],
) -> dict[str, float]:
    """Proyecta tiempos y energía al volumen real del banco.

    Args:
        por_tamano: resultados del experimento contra n.
        dia_real: resultados del día medido con el volumen real.
        calidad: resultados del experimento de llenado.

    Returns:
        Los tiempos estimados, la energía por día y por año, y los kilogramos
        y el CO2 relacionados con la diferencia de llenado.
    """
    exh = por_tamano["exhaustivo"][max(TAMANOS_EXHAUSTIVO)]
    n_max = max(TAMANOS_EXHAUSTIVO)
    seg_por_revision = exh["tiempo_s"] / exh["operaciones"]
    # Instancia típica: 450 lotes. Tiempo = revisiones * n * 2^n.
    n_tipico = 450
    log10_s = (math.log10(seg_por_revision) + math.log10(n_tipico)
               + n_tipico * math.log10(2))
    grande = por_tamano["estrategia"][max(TAMANOS_ESTRATEGIA)]
    seg_por_celda = grande["tiempo_s"] / grande["operaciones"]
    t_dp = dia_real["tiempo_estrategia_s"]
    t_regla = dia_real["tiempo_regla_s"]
    kwh_dp = POTENCIA_KW * t_dp / 3600
    kwh_regla = POTENCIA_KW * t_regla / 3600
    kg_extra = calidad["kg_extra_por_dia"]
    return {
        "segundos_por_celda": seg_por_celda,
        "segundos_por_revision_exhaustivo": seg_por_revision,
        "n_maximo_exhaustivo": n_max,
        "log10_segundos_exhaustivo_n450": log10_s,
        "log10_anios_exhaustivo_n450": log10_s - math.log10(3.15e7),
        "tiempo_dia_estrategia_s": t_dp,
        "tiempo_dia_regla_s": t_regla,
        "fraccion_ventana_estrategia": t_dp / VENTANA_S,
        "kwh_dia_estrategia": kwh_dp,
        "kwh_dia_regla": kwh_regla,
        "kwh_anio_estrategia": kwh_dp * DIAS_ANIO,
        "kwh_anio_regla": kwh_regla * DIAS_ANIO,
        "kwh_anio_diferencia": (kwh_dp - kwh_regla) * DIAS_ANIO,
        "kg_extra_por_dia": kg_extra,
        "kg_extra_por_anio": kg_extra * DIAS_ANIO,
        "co2_kg_anio_si_10pct_se_perdia": (
            0.10 * kg_extra * DIAS_ANIO * CO2_POR_KG
        ),
        "co2_kg_anio_computo_diferencia": (
            (kwh_dp - kwh_regla) * DIAS_ANIO * CO2_POR_KWH
        ),
    }


def graficar(
    por_tamano: dict[str, dict[int, dict[str, float]]],
    por_capacidad: dict[int, dict[str, float]],
) -> None:
    """Guarda las tres gráficas de la operación.

    Args:
        por_tamano: resultados del experimento contra n.
        por_capacidad: resultados del experimento contra W.
    """
    CARPETA_GRAFICAS.mkdir(parents=True, exist_ok=True)
    etiquetas = {
        "estrategia": "Programación dinámica (estrategia)",
        "exhaustivo": "Exhaustivo",
        "vencimiento": "Por vencimiento (regla actual)",
        "densidad": "Por densidad",
    }
    for llave, titulo, eje, archivo in (
        ("tiempo_s", "Tiempo de cargue de un vehículo según el número de "
         "lotes", "Tiempo medio (s)", "tiempo_vs_n.png"),
        ("operaciones", "Operaciones elementales según el número de lotes",
         "Operaciones elementales", "operaciones_vs_n.png"),
    ):
        plt.figure(figsize=(8, 5))
        for nombre, datos in por_tamano.items():
            xs = sorted(datos)
            plt.plot(xs, [datos[x][llave] for x in xs], marker="o",
                     label=etiquetas[nombre])
        plt.xscale("log")
        plt.yscale("log")
        plt.title(titulo + f" (capacidad {CAPACIDAD_FIJA} kg)")
        plt.xlabel("Número de lotes candidatos, n (lotes)")
        plt.ylabel(eje)
        plt.grid(True, which="both", alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(CARPETA_GRAFICAS / archivo, dpi=130)
        plt.close()
    plt.figure(figsize=(8, 5))
    ws = sorted(por_capacidad)
    plt.plot(ws, [por_capacidad[w]["tiempo_s"] for w in ws], marker="o",
             label=f"Programación dinámica, n = {LOTES_FIJOS} lotes")
    plt.xscale("log")
    plt.yscale("log")
    plt.title("Tiempo de la estrategia con n fijo y capacidad creciente")
    plt.xlabel("Capacidad del vehículo, W (kg)")
    plt.ylabel("Tiempo medio (s)")
    plt.grid(True, which="both", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(CARPETA_GRAFICAS / "tiempo_vs_capacidad.png", dpi=130)
    plt.close()


def main() -> None:
    """Corre todos los experimentos, guarda gráficas y resultados."""
    print("Midiendo contra el número de lotes...")
    por_tamano = experimento_tamano()
    print("Midiendo contra la capacidad...")
    por_capacidad = experimento_capacidad()
    print("Comparando llenado y valor en días simulados...")
    calidad = experimento_calidad()
    print("Ejecutando un día con el volumen real...")
    dia_real = experimento_dia_real()
    proyeccion = extrapolar(por_tamano, dia_real, calidad)
    graficar(por_tamano, por_capacidad)
    ARCHIVO_RESULTADOS.parent.mkdir(exist_ok=True)
    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as archivo:
        json.dump({"por_tamano": por_tamano, "por_capacidad": por_capacidad,
                   "calidad": calidad, "dia_real": dia_real,
                   "proyeccion": proyeccion}, archivo, indent=2)
    print("Listo: gráficas y resultados guardados.")


if __name__ == "__main__":
    main()
