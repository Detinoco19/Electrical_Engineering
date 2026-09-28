
import pandas as pd

from scripts.analisis_motores import (
    procesar_motores,
    procesar_historial,
    generar_resumen,
    generar_control_calidad,
)

PARAMETROS = {
    "carga_baja_pct": 30,
    "carga_alta_pct": 90,
    "sobrecarga_pct": 100,
    "desbalance_corriente_alerta_pct": 5,
    "desbalance_voltaje_alerta_pct": 1,
}

def crear_motores():
    return pd.DataFrame(
        [
            {
                "TAG": "M-001",
                "DESCRIPCION": "Motor WEG 1",
                "AREA": "SECADO",
                "FABRICANTE": "WEG",
                "MODELO": "W22 Premium",
                "SERIE": "SERIE-001",
                "TIPO_EQUIPO": "Motor de inducción jaula",
                "KW_PLACA": 9.2,
                "HP": 12.33,
                "VOLTAJE_V": 480,
                "CORRIENTE_PLACA_A": 14.3,
                "VOLTAJE_PLACA_1_V": 240,
                "CORRIENTE_PLACA_1_A": 28.6,
                "VOLTAJE_PLACA_2_V": 480,
                "CORRIENTE_PLACA_2_A": 14.3,
                "FRECUENCIA_HZ": 60,
                "FP": 0.84,
                "EFICIENCIA": 0.924,
                "ESTADO": "Operativo",
                "FUENTE_DATOS": "PLACA",
                "OBSERVACIONES": "",
            },
            {
                "TAG": "M-002",
                "DESCRIPCION": "Motor WEG 2",
                "AREA": "SECADO",
                "FABRICANTE": "WEG",
                "MODELO": "W22 Premium",
                "SERIE": "SERIE-002",
                "TIPO_EQUIPO": "Motor de inducción jaula",
                "KW_PLACA": 9.2,
                "HP": 12.33,
                "VOLTAJE_V": 480,
                "CORRIENTE_PLACA_A": 14.3,
                "VOLTAJE_PLACA_1_V": 240,
                "CORRIENTE_PLACA_1_A": 28.6,
                "VOLTAJE_PLACA_2_V": 480,
                "CORRIENTE_PLACA_2_A": 14.3,
                "FRECUENCIA_HZ": 60,
                "FP": 0.84,
                "EFICIENCIA": 0.924,
                "ESTADO": "Operativo",
                "FUENTE_DATOS": "PLACA",
                "OBSERVACIONES": "",
            },
        ]
    )

def crear_mediciones():
    return pd.DataFrame(
        [
            {
                "FECHA": "01/09/2026",
                "TAG": "M-001",
                "CORRIENTE_L1_A": 11.8,
                "CORRIENTE_L2_A": 12.0,
                "CORRIENTE_L3_A": 12.2,
                "VOLTAJE_L1_L2_V": 479,
                "VOLTAJE_L2_L3_V": 480,
                "VOLTAJE_L3_L1_V": 481,
                "TEMPERATURA_C": None,
                "AISLAMIENTO_MOHM": None,
                "ESTADO": "Operando",
                "OBSERVACIONES": "",
            },
            {
                "FECHA": "27/09/2026",
                "TAG": "M-001",
                "CORRIENTE_L1_A": 11.9,
                "CORRIENTE_L2_A": 12.0,
                "CORRIENTE_L3_A": 12.1,
                "VOLTAJE_L1_L2_V": 479,
                "VOLTAJE_L2_L3_V": 480,
                "VOLTAJE_L3_L1_V": 481,
                "TEMPERATURA_C": None,
                "AISLAMIENTO_MOHM": None,
                "ESTADO": "Operando",
                "OBSERVACIONES": "",
            },
        ]
    )

def test_usa_ultima_medicion():
    resultado = procesar_motores(crear_motores(), crear_mediciones(), PARAMETROS)
    fila = resultado.loc[resultado["TAG"] == "M-001"].iloc[0]
    assert fila["FECHA"].strftime("%d/%m/%Y") == "27/09/2026"

def test_corriente_promedio():
    resultado = procesar_motores(crear_motores(), crear_mediciones(), PARAMETROS)
    fila = resultado.loc[resultado["TAG"] == "M-001"].iloc[0]
    assert fila["CORRIENTE_PROMEDIO_A"] == 12.0

def test_motor_con_medicion():
    resultado = procesar_motores(crear_motores(), crear_mediciones(), PARAMETROS)
    fila = resultado.loc[resultado["TAG"] == "M-001"].iloc[0]
    assert bool(fila["TIENE_MEDICION"])

def test_motor_sin_medicion():
    resultado = procesar_motores(crear_motores(), crear_mediciones(), PARAMETROS)
    fila = resultado.loc[resultado["TAG"] == "M-002"].iloc[0]
    assert not bool(fila["TIENE_MEDICION"])
    assert fila["DIAGNOSTICO_GENERAL"] == "SIN MEDICION"

def test_resumen():
    resultado = procesar_motores(crear_motores(), crear_mediciones(), PARAMETROS)
    resumen = generar_resumen(resultado, PARAMETROS)
    valores = dict(zip(resumen["INDICADOR"], resumen["VALOR"]))
    assert valores["Total de motores"] == 2
    assert valores["Motores con medición"] == 1
    assert valores["Motores sin medición"] == 1

def test_historial_conserva_todas_mediciones():
    historial = procesar_historial(crear_motores(), crear_mediciones(), PARAMETROS)
    assert len(historial) == 2
    assert historial.iloc[0]["FECHA"].strftime("%d/%m/%Y") == "01/09/2026"
    assert historial.iloc[1]["FECHA"].strftime("%d/%m/%Y") == "27/09/2026"

def test_diagnostico_normal():
    resultado = procesar_motores(crear_motores(), crear_mediciones(), PARAMETROS)
    fila = resultado.loc[resultado["TAG"] == "M-001"].iloc[0]
    assert fila["DIAGNOSTICO_GENERAL"] == "NORMAL"

def test_calidad_detecta_serie_duplicada():
    motores = crear_motores()
    motores.loc[motores["TAG"] == "M-002", "SERIE"] = "SERIE-001"
    calidad = generar_control_calidad(motores, crear_mediciones())
    hallazgos = calidad[calidad["TIPO"] == "SERIE_DUPLICADA"]
    assert len(hallazgos) == 2
