from scripts.motores import hp_a_kw
from scripts.motores import corriente_motor_trifasico


def test_conversion_hp_kw():
    resultado = hp_a_kw(100)

    assert abs(resultado - 74.6) < 0.001


def test_corriente_motor():
    resultado = corriente_motor_trifasico(
        hp=125,
        voltaje=480,
        factor_potencia=0.88,
        eficiencia=0.94,
    )

    assert abs(resultado - 135.59) < 0.1