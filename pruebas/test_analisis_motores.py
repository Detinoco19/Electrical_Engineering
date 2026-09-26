import pandas as pd

from scripts.analisis_motores import (
    procesar_motores,
    generar_resumen,
)


PARAMETROS = {
    "carga_baja_pct": 30,
    "carga_alta_pct": 90,
    "sobrecarga_pct": 100,
    "desbalance_corriente_alerta_pct": 5,
    "desbalance_voltaje_alerta_pct": 1,
}


def crear_motor_prueba():

    return pd.DataFrame(
        [
            {
                "TAG": "M-001",
                "DESCRIPCION": "Bomba",
                "HP": 125,
                "VOLTAJE": 480,
                "FP": 0.88,
                "EFICIENCIA": 0.94,
                "CORRIENTE_PLACA_A": 140,
                "CORRIENTE_L1_A": 118,
                "CORRIENTE_L2_A": 120,
                "CORRIENTE_L3_A": 123,
                "VOLTAJE_L1_L2_V": 478,
                "VOLTAJE_L2_L3_V": 481,
                "VOLTAJE_L3_L1_V": 479,
                "ESTADO": "Operando",
            }
        ]
    )


def test_procesar_motor():

    datos = crear_motor_prueba()

    resultado = procesar_motores(
        datos,
        PARAMETROS,
    )

    motor = resultado.iloc[0]

    assert abs(
        motor["CORRIENTE_PROMEDIO_A"]
        - 120.33
    ) < 0.01

    assert abs(
        motor["CARGA_CORRIENTE_PCT"]
        - 85.95
    ) < 0.01

    assert motor[
        "FASE_MAYOR_CORRIENTE"
    ] == "L3"

    assert motor[
        "DIAGNOSTICO_GENERAL"
    ] == "NORMAL"


def test_generar_resumen():

    datos = crear_motor_prueba()

    resultado = procesar_motores(
        datos,
        PARAMETROS,
    )

    resumen = generar_resumen(
        resultado,
        PARAMETROS,
    )

    valores = dict(
        zip(
            resumen["INDICADOR"],
            resumen["VALOR"],
        )
    )

    assert (
        valores["Total de motores"]
        == 1
    )

    assert (
        valores[
            "Motores diagnóstico normal"
        ]
        == 1
    )