"""Generador de series sintéticas del cambio neto de inventario por hora.

Cada función recibe una semilla y usa su propio generador aleatorio, así
que la misma semilla siempre produce la misma serie.
"""

import random


def generar_serie(n: int, semilla: int) -> list[int]:
    """Genera una serie de n horas con temporadas de acumulación.

    El inventario de una categoría sube y baja de forma irregular (entre
    -150 y 150 kg por hora, con un leve sesgo a la baja) y de vez en cuando
    hay una temporada con entradas altas, que es el tramo que busca la
    Dirección.

    Args:
        n: número de horas de la serie.
        semilla: semilla del generador aleatorio.

    Returns:
        El cambio neto del inventario en cada hora, en kilogramos.
    """
    rng = random.Random(semilla)
    serie = [rng.randint(-160, 150) for _ in range(n)]
    horas_por_temporada = max(50, n // 10)
    for inicio in range(0, n, horas_por_temporada * 3):
        largo = rng.randint(horas_por_temporada // 2, horas_por_temporada)
        for i in range(inicio, min(n, inicio + largo)):
            serie[i] += rng.randint(40, 120)
    return serie


def generar_serie_pequena(n: int, semilla: int) -> list[int]:
    """Genera una serie corta con valores chicos para las pruebas.

    Args:
        n: número de horas de la serie.
        semilla: semilla del generador aleatorio.

    Returns:
        Una lista de n enteros entre -20 y 20.
    """
    rng = random.Random(semilla)
    return [rng.randint(-20, 20) for _ in range(n)]
