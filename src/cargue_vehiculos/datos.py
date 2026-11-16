"""Generador de datos sintéticos para el cargue de vehículos.

Todas las funciones reciben una semilla y usan su propio generador
aleatorio, así que la misma semilla siempre produce las mismas instancias.
"""

import random

from estrategia import Lote

# Prioridad nutricional de la categoría: otros, frutas y verduras, proteína.
PRIORIDADES = (1, 2, 3)
PESOS_PRIORIDAD = (0.5, 0.3, 0.2)


def generar_lotes(n: int, semilla: int) -> list[Lote]:
    """Genera n lotes con la estructura que describe el caso.

    La mitad de los lotes son livianos (cajas, hasta 250 kg) y la otra
    mitad pesados (estibas, hasta 2.000 kg). Se escogió esa mezcla para que
    cargar por vencimiento llene en promedio cerca del 78 % que informa el
    cliente. El valor nutricional es el peso por las raciones
    por kilogramo, multiplicado por la prioridad de la categoría.

    Args:
        n: número de lotes candidatos.
        semilla: semilla del generador aleatorio.

    Returns:
        Una lista de tuplas (peso_kg, valor_nutricional, dias_para_vencer).
    """
    rng = random.Random(semilla)
    lotes: list[Lote] = []
    for _ in range(n):
        if rng.random() < 0.5:
            peso = rng.randint(15, 250)
        else:
            peso = rng.randint(250, 2000)
        prioridad = rng.choices(PRIORIDADES, PESOS_PRIORIDAD)[0]
        raciones_por_kg = rng.uniform(1.5, 5.0)
        valor = max(1, round(peso * raciones_por_kg * prioridad))
        dias = rng.randint(1, 21)
        lotes.append((peso, valor, dias))
    return lotes


def generar_lotes_pequenos(n: int, semilla: int) -> list[Lote]:
    """Genera lotes de pesos y valores chicos para las pruebas.

    Args:
        n: número de lotes candidatos.
        semilla: semilla del generador aleatorio.

    Returns:
        Una lista de tuplas (peso_kg, valor_nutricional, dias_para_vencer).
    """
    rng = random.Random(semilla)
    return [
        (rng.randint(1, 20), rng.randint(1, 60), rng.randint(1, 15))
        for _ in range(n)
    ]


def generar_capacidades(semilla: int, vehiculos: int = 14) -> list[int]:
    """Genera las capacidades de la flota (entre 2.500 y 4.000 kg).

    Args:
        semilla: semilla del generador aleatorio.
        vehiculos: número de vehículos de la flota.

    Returns:
        La capacidad en kilogramos de cada vehículo.
    """
    rng = random.Random(semilla)
    return [rng.randint(2500, 4000) for _ in range(vehiculos)]


def generar_dia(semilla: int) -> list[tuple[list[Lote], int]]:
    """Genera un día completo de planeación con los volúmenes del caso.

    Args:
        semilla: semilla del generador aleatorio.

    Returns:
        Una lista con una pareja (lotes de la ruta, capacidad) por cada uno
        de los 14 vehículos; cada ruta tiene entre 300 y 600 lotes.
    """
    rng = random.Random(semilla)
    dia = []
    for k, capacidad in enumerate(generar_capacidades(semilla)):
        n = rng.randint(300, 600)
        dia.append((generar_lotes(n, semilla * 100 + k), capacidad))
    return dia
