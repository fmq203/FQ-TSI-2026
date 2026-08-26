"""Archivo de prueba para validar la regla no-eval-python (Actividad 07).

No forma parte de ningún sistema en producción: existe solo para demostrar
que la regla detecta el patrón prohibido antes de aplicarla sobre código real.
"""


def calcular_descuento(expresion_usuario: str) -> float:
    # Patrón inseguro deliberado: eval() sobre un valor que podría venir de un formulario web.
    return eval(expresion_usuario)


def calcular_descuento_seguro(porcentaje: float, monto: float) -> float:
    return monto * (porcentaje / 100)
