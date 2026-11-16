"""Solución exhaustiva del cargue: prueba todos los subconjuntos de lotes.

Solo sirve para instancias pequeñas porque su costo es exponencial. En el
proyecto se usa para comprobar que la programación dinámica sí da el
máximo.
"""

from estrategia import Lote, validar_entrada


def cargar_exhaustivo(
    lotes: list[Lote],
    capacidad_kg: int,
    contador: list[int] | None = None,
) -> tuple[int, list[int]]:
    """Calcula el mismo resultado probando todos los subconjuntos de lotes.

    Cada subconjunto se representa con una máscara de bits: el bit ``i``
    encendido significa que el lote ``i`` sube al vehículo. Si hay varios
    subconjuntos con el mismo valor máximo se queda con el primero que
    encuentra.

    Args:
        lotes: lotes candidatos de la ruta.
        capacidad_kg: capacidad máxima del vehículo en kilogramos.
        contador: lista de un elemento donde se suma el número de lotes
            revisados (n por cada subconjunto). Es opcional y solo sirve
            para las mediciones.

    Returns:
        El valor nutricional máximo y los índices de los lotes cargados,
        en orden creciente.
    """
    validar_entrada(lotes, capacidad_kg)
    n = len(lotes)
    mejor_valor = 0
    mejor_mascara = 0
    for mascara in range(1 << n):
        peso_total = 0
        valor_total = 0
        for i in range(n):
            if mascara >> i & 1:
                peso_total += lotes[i][0]
                valor_total += lotes[i][1]
        if peso_total <= capacidad_kg and valor_total > mejor_valor:
            mejor_valor = valor_total
            mejor_mascara = mascara
        if contador is not None:
            contador[0] += n
    elegidos = [i for i in range(n) if mejor_mascara >> i & 1]
    return mejor_valor, elegidos
