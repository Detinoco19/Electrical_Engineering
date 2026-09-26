from scripts.motores import (
    hp_a_kw,
    corriente_motor_trifasico,
    promedio_trifasico,
    desbalance_porcentual,
    fase_mayor,
    fase_menor,
)


# ============================================================
# PRUEBA 1
# CONVERSIÓN HP → kW
# ============================================================

def test_conversion_hp_kw():

    resultado = hp_a_kw(
        100
    )

    assert abs(
        resultado - 74.6
    ) < 0.001


# ============================================================
# PRUEBA 2
# CORRIENTE DE MOTOR TRIFÁSICO
# ============================================================

def test_corriente_motor():

    resultado = corriente_motor_trifasico(
        hp=125,
        voltaje=480,
        factor_potencia=0.88,
        eficiencia=0.94,
    )

    assert abs(
        resultado - 135.59
    ) < 0.1


# ============================================================
# PRUEBA 3
# PROMEDIO TRIFÁSICO
# ============================================================

def test_promedio_trifasico():

    resultado = promedio_trifasico(
        118,
        120,
        122,
    )

    assert abs(
        resultado - 120
    ) < 0.001


# ============================================================
# PRUEBA 4
# DESBALANCE PORCENTUAL
# ============================================================

def test_desbalance_porcentual():

    resultado = desbalance_porcentual(
        118,
        120,
        122,
    )

    assert abs(
        resultado - 1.6667
    ) < 0.01


# ============================================================
# PRUEBA 5
# FASE CON MAYOR CORRIENTE
# ============================================================

def test_fase_mayor():

    resultado = fase_mayor(
        118,
        120,
        123,
    )

    assert resultado == "L3"


# ============================================================
# PRUEBA 6
# FASE CON MENOR CORRIENTE
# ============================================================

def test_fase_menor():

    resultado = fase_menor(
        118,
        120,
        123,
    )

    assert resultado == "L1"