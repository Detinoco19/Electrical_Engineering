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


# ============================================================
# DATOS DE PRUEBA
# ============================================================

def crear_motor():

    return pd.DataFrame(
        [
            {
                "TAG": "MR-001",
                "DESCRIPCION": "Motorreductor",
                "AREA": "SECADO MECANICO",
                "FABRICANTE": "SEW-EURODRIVE",
                "MODELO": "R97 DRN100L4/BES",
                "TIPO_EQUIPO": "Motorreductor",
                "KW_PLACA": 3.7,
                "HP": 4.96,
                "VOLTAJE_V": 480,
                "CORRIENTE_PLACA_A": 6.90,
                "FRECUENCIA_HZ": 60,
                "FP": 0.72,
                "EFICIENCIA": 0.895,
                "ESTADO": "Operativo",
                "OBSERVACIONES": "",
            }
        ]
    )


def crear_mediciones():

    return pd.DataFrame(
        [
            {
                "FECHA": "27/09/2026",
                "TAG": "MR-001",
                "CORRIENTE_L1_A": 5.8,
                "CORRIENTE_L2_A": 5.9,
                "CORRIENTE_L3_A": 6.0,
                "VOLTAJE_L1_L2_V": 478,
                "VOLTAJE_L2_L3_V": 480,
                "VOLTAJE_L3_L1_V": 479,
                "TEMPERATURA_C": 52,
                "AISLAMIENTO_MOHM": 850,
                "ESTADO": "Operando",
                "OBSERVACIONES": "",
            },

            {
                "FECHA": "27/10/2026",
                "TAG": "MR-001",
                "CORRIENTE_L1_A": 5.9,
                "CORRIENTE_L2_A": 6.0,
                "CORRIENTE_L3_A": 6.1,
                "VOLTAJE_L1_L2_V": 479,
                "VOLTAJE_L2_L3_V": 480,
                "VOLTAJE_L3_L1_V": 481,
                "TEMPERATURA_C": 53,
                "AISLAMIENTO_MOHM": 820,
                "ESTADO": "Operando",
                "OBSERVACIONES": "",
            },
        ]
    )


# ============================================================
# PRUEBA ÚLTIMA MEDICIÓN
# ============================================================

def test_ultima_medicion():

    resultado = procesar_motores(
        crear_motor(),
        crear_mediciones(),
        PARAMETROS,
    )

    motor = resultado.iloc[0]

    assert (
        motor["FECHA"].strftime(
            "%d/%m/%Y"
        )
        == "27/10/2026"
    )


# ============================================================
# PRUEBA CORRIENTE PROMEDIO
# ============================================================

def test_corriente_promedio():

    resultado = procesar_motores(
        crear_motor(),
        crear_mediciones(),
        PARAMETROS,
    )

    motor = resultado.iloc[0]

    assert abs(
        motor["CORRIENTE_PROMEDIO_A"]
        - 6.0
    ) < 0.01


# ============================================================
# PRUEBA DETECCIÓN DE MEDICIÓN
# ============================================================

def test_motor_con_medicion():

    resultado = procesar_motores(
        crear_motor(),
        crear_mediciones(),
        PARAMETROS,
    )

    motor = resultado.iloc[0]

    assert bool(
        motor["TIENE_MEDICION"]
    )


# ============================================================
# PRUEBA DEL RESUMEN
# ============================================================

def test_resumen():

    resultado = procesar_motores(
        crear_motor(),
        crear_mediciones(),
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
        valores["Motores con medición"]
        == 1
    )

    assert (
        valores["Motores sin medición"]
        == 0
    )