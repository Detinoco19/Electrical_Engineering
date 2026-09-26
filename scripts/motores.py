import math


# ============================================================
# CONSTANTES
# ============================================================

HP_A_KW = 0.746


# ============================================================
# CONVERSIÓN DE POTENCIA
# ============================================================

def hp_a_kw(hp: float) -> float:
    """
    Convertir potencia mecánica de HP a kW.

    Parámetros
    ----------
    hp : float
        Potencia en horsepower.

    Retorna
    -------
    float
        Potencia equivalente en kW.
    """

    if hp <= 0:
        raise ValueError(
            "HP debe ser mayor que cero."
        )

    return hp * HP_A_KW


# ============================================================
# CORRIENTE DE MOTOR TRIFÁSICO
# ============================================================

def corriente_motor_trifasico(
    hp: float,
    voltaje: float,
    factor_potencia: float,
    eficiencia: float,
) -> float:
    """
    Calcular corriente estimada de un motor trifásico.

    Fórmula:

        I = P / (sqrt(3) * V * FP * eficiencia)

    donde la potencia mecánica en HP se convierte primero
    a watts.

    Parámetros
    ----------
    hp : float
        Potencia mecánica del motor en HP.

    voltaje : float
        Voltaje línea-línea en V.

    factor_potencia : float
        Factor de potencia decimal.
        Ejemplo: 0.88.

    eficiencia : float
        Eficiencia decimal.
        Ejemplo: 0.94.

    Retorna
    -------
    float
        Corriente estimada en amperios.
    """

    if hp <= 0:
        raise ValueError(
            "HP debe ser mayor que cero."
        )

    if voltaje <= 0:
        raise ValueError(
            "Voltaje debe ser mayor que cero."
        )

    if not 0 < factor_potencia <= 1:
        raise ValueError(
            "Factor de potencia debe estar entre 0 y 1."
        )

    if not 0 < eficiencia <= 1:
        raise ValueError(
            "Eficiencia debe estar entre 0 y 1."
        )

    potencia_salida_w = (
        hp_a_kw(hp)
        * 1000
    )

    corriente = (
        potencia_salida_w
        /
        (
            math.sqrt(3)
            * voltaje
            * factor_potencia
            * eficiencia
        )
    )

    return corriente


# ============================================================
# PROMEDIO TRIFÁSICO
# ============================================================

def promedio_trifasico(
    valor_1: float,
    valor_2: float,
    valor_3: float,
) -> float:
    """
    Calcular promedio aritmético de tres mediciones.

    Puede utilizarse para:

    - Corrientes L1, L2 y L3.
    - Voltajes L1-L2, L2-L3 y L3-L1.
    """

    valores = [
        valor_1,
        valor_2,
        valor_3,
    ]

    if any(
        valor < 0
        for valor in valores
    ):
        raise ValueError(
            "Las mediciones no pueden ser negativas."
        )

    promedio = (
        sum(valores)
        / 3
    )

    return promedio


# ============================================================
# DESBALANCE PORCENTUAL
# ============================================================

def desbalance_porcentual(
    valor_1: float,
    valor_2: float,
    valor_3: float,
) -> float:
    """
    Calcular el máximo desbalance porcentual respecto
    al promedio de tres mediciones.

    Fórmula:

        Desbalance (%) =
        máxima desviación respecto al promedio
        -------------------------------------- x 100
                     promedio
    """

    promedio = promedio_trifasico(
        valor_1,
        valor_2,
        valor_3,
    )

    if promedio == 0:
        raise ValueError(
            "No se puede calcular desbalance "
            "con promedio igual a cero."
        )

    desviacion_1 = abs(
        valor_1 - promedio
    )

    desviacion_2 = abs(
        valor_2 - promedio
    )

    desviacion_3 = abs(
        valor_3 - promedio
    )

    desviacion_maxima = max(
        desviacion_1,
        desviacion_2,
        desviacion_3,
    )

    desbalance = (
        desviacion_maxima
        / promedio
        * 100
    )

    return desbalance


# ============================================================
# IDENTIFICACIÓN DE FASE CON MAYOR VALOR
# ============================================================

def fase_mayor(
    valor_l1: float,
    valor_l2: float,
    valor_l3: float,
) -> str:
    """
    Identificar la fase que presenta el mayor valor.
    """

    valores = {
        "L1": valor_l1,
        "L2": valor_l2,
        "L3": valor_l3,
    }

    return max(
        valores,
        key=valores.get,
    )


# ============================================================
# IDENTIFICACIÓN DE FASE CON MENOR VALOR
# ============================================================

def fase_menor(
    valor_l1: float,
    valor_l2: float,
    valor_l3: float,
) -> str:
    """
    Identificar la fase que presenta el menor valor.
    """

    valores = {
        "L1": valor_l1,
        "L2": valor_l2,
        "L3": valor_l3,
    }

    return min(
        valores,
        key=valores.get,
    )


# ============================================================
# PRUEBA MANUAL
# ============================================================

if __name__ == "__main__":

    corriente = corriente_motor_trifasico(
        hp=125,
        voltaje=480,
        factor_potencia=0.88,
        eficiencia=0.94,
    )

    corriente_promedio = promedio_trifasico(
        118,
        120,
        123,
    )

    desbalance_corriente = desbalance_porcentual(
        118,
        120,
        123,
    )

    print()
    print("PRUEBA DE MOTOR")
    print("=" * 40)

    print(
        f"Corriente calculada: "
        f"{corriente:.2f} A"
    )

    print(
        f"Corriente promedio: "
        f"{corriente_promedio:.2f} A"
    )

    print(
        f"Desbalance corriente: "
        f"{desbalance_corriente:.2f} %"
    )

    print(
        f"Fase mayor corriente: "
        f"{fase_mayor(118, 120, 123)}"
    )

    print(
        f"Fase menor corriente: "
        f"{fase_menor(118, 120, 123)}"
    )