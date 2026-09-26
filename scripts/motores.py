import math


def hp_a_kw(hp: float) -> float:
    """Convertir potencia mecánica de HP a kW."""
    if hp <= 0:
        raise ValueError("HP debe ser mayor que cero.")

    return hp * 0.746


def corriente_motor_trifasico(
    hp: float,
    voltaje: float,
    factor_potencia: float,
    eficiencia: float,
) -> float:
    """
    Calcular corriente estimada de un motor trifásico.

    Parámetros
    ----------
    hp:
        Potencia mecánica del motor en HP.
    voltaje:
        Voltaje línea-línea en V.
    factor_potencia:
        Factor de potencia decimal. Ejemplo: 0.88.
    eficiencia:
        Eficiencia decimal. Ejemplo: 0.94.

    Retorna
    -------
    float
        Corriente estimada en amperios.
    """

    if voltaje <= 0:
        raise ValueError("Voltaje debe ser mayor que cero.")

    if not 0 < factor_potencia <= 1:
        raise ValueError(
            "Factor de potencia debe estar entre 0 y 1."
        )

    if not 0 < eficiencia <= 1:
        raise ValueError(
            "Eficiencia debe estar entre 0 y 1."
        )

    potencia_salida_w = hp_a_kw(hp) * 1000

    corriente = potencia_salida_w / (
        math.sqrt(3)
        * voltaje
        * factor_potencia
        * eficiencia
    )

    return corriente


if __name__ == "__main__":

    corriente = corriente_motor_trifasico(
        hp=125,
        voltaje=480,
        factor_potencia=0.88,
        eficiencia=0.94,
    )

    print("MOTOR TRIFASICO")
    print("----------------")
    print("Potencia: 125 HP")
    print("Voltaje: 480 V")
    print("FP: 0.88")
    print("Eficiencia: 0.94")
    print(f"Corriente estimada: {corriente:.2f} A")