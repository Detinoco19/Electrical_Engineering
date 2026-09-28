
import math

HP_A_KW = 0.746

def hp_a_kw(hp):
    if hp <= 0:
        raise ValueError("HP debe ser mayor que cero.")
    return hp * HP_A_KW

def corriente_motor_trifasico(hp, voltaje, factor_potencia, eficiencia):
    if hp <= 0:
        raise ValueError("HP debe ser mayor que cero.")
    if voltaje <= 0:
        raise ValueError("Voltaje debe ser mayor que cero.")
    if not 0 < factor_potencia <= 1:
        raise ValueError("Factor de potencia debe estar entre 0 y 1.")
    if not 0 < eficiencia <= 1:
        raise ValueError("Eficiencia debe estar entre 0 y 1.")
    potencia_salida_w = hp_a_kw(hp) * 1000
    return potencia_salida_w / (
        math.sqrt(3) * voltaje * factor_potencia * eficiencia
    )

def promedio_trifasico(v1, v2, v3):
    valores = [v1, v2, v3]
    if any(v < 0 for v in valores):
        raise ValueError("Las mediciones no pueden ser negativas.")
    return sum(valores) / 3

def desbalance_porcentual(v1, v2, v3):
    promedio = promedio_trifasico(v1, v2, v3)
    if promedio == 0:
        raise ValueError("No se puede calcular desbalance con promedio cero.")
    desviacion_maxima = max(
        abs(v1 - promedio),
        abs(v2 - promedio),
        abs(v3 - promedio),
    )
    return desviacion_maxima / promedio * 100

def fase_mayor(v1, v2, v3):
    valores = {"L1": v1, "L2": v2, "L3": v3}
    return max(valores, key=valores.get)

def fase_menor(v1, v2, v3):
    valores = {"L1": v1, "L2": v2, "L3": v3}
    return min(valores, key=valores.get)
