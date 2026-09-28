
import pytest
from scripts.motores import (
    hp_a_kw,
    corriente_motor_trifasico,
    promedio_trifasico,
    desbalance_porcentual,
    fase_mayor,
    fase_menor,
)

def test_conversion_hp_kw():
    assert hp_a_kw(100) == pytest.approx(74.6)

def test_corriente_motor():
    assert corriente_motor_trifasico(125, 480, 0.88, 0.94) == pytest.approx(135.6, abs=0.2)

def test_promedio_trifasico():
    assert promedio_trifasico(118, 120, 122) == pytest.approx(120)

def test_desbalance_porcentual():
    assert desbalance_porcentual(118, 120, 122) == pytest.approx(1.6667, abs=0.01)

def test_fase_mayor():
    assert fase_mayor(118, 120, 123) == "L3"

def test_fase_menor():
    assert fase_menor(118, 120, 123) == "L1"
