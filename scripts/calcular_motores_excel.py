from pathlib import Path

import pandas as pd

from scripts.motores import (
    hp_a_kw,
    corriente_motor_trifasico,
)


# ============================================================
# RUTAS
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

ARCHIVO_ENTRADA = RAIZ / "datos" / "motores.xlsx"

ARCHIVO_SALIDA = (
    RAIZ / "resultados" / "motores_calculados.xlsx"
)


# ============================================================
# EVALUACIÓN
# ============================================================

def evaluar_motor(fila):
    """
    Evaluar la corriente medida respecto a la corriente de placa.

    Nota:
    CARGA_CORRIENTE_PCT es un indicador basado en corriente.
    No representa directamente la carga mecánica real del motor.
    """

    carga = fila["CARGA_CORRIENTE_PCT"]

    if carga > 100:
        return "REVISAR SOBRECARGA"

    if carga > 90:
        return "CARGA ALTA"

    if carga < 30:
        return "CARGA BAJA"

    return "NORMAL"


# ============================================================
# CÁLCULO PRINCIPAL
# ============================================================

def calcular_motores():
    """Leer Excel, calcular parámetros y generar resultados."""

    # Leer archivo
    df = pd.read_excel(ARCHIVO_ENTRADA)

    # Columnas obligatorias
    columnas_requeridas = {
        "TAG",
        "DESCRIPCION",
        "HP",
        "VOLTAJE",
        "FP",
        "EFICIENCIA",
        "CORRIENTE_PLACA_A",
        "CORRIENTE_MEDIDA_A",
        "ESTADO",
    }

    faltantes = columnas_requeridas - set(df.columns)

    if faltantes:
        raise ValueError(
            f"Faltan columnas en motores.xlsx: {sorted(faltantes)}"
        )

    # --------------------------------------------------------
    # Potencia
    # --------------------------------------------------------

    df["KW"] = df["HP"].apply(hp_a_kw)

    # --------------------------------------------------------
    # Corriente calculada
    # --------------------------------------------------------

    df["CORRIENTE_CALCULADA_A"] = df.apply(
        lambda fila: corriente_motor_trifasico(
            hp=fila["HP"],
            voltaje=fila["VOLTAJE"],
            factor_potencia=fila["FP"],
            eficiencia=fila["EFICIENCIA"],
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # Comparación cálculo vs placa
    # --------------------------------------------------------

    df["DESVIACION_CALC_PLACA_PCT"] = (
        (
            df["CORRIENTE_CALCULADA_A"]
            - df["CORRIENTE_PLACA_A"]
        )
        / df["CORRIENTE_PLACA_A"]
        * 100
    )

    # --------------------------------------------------------
    # Indicador de carga por corriente
    # --------------------------------------------------------

    df["CARGA_CORRIENTE_PCT"] = (
        df["CORRIENTE_MEDIDA_A"]
        / df["CORRIENTE_PLACA_A"]
        * 100
    )

    # --------------------------------------------------------
    # Evaluación
    # --------------------------------------------------------

    df["ALERTA"] = df.apply(
        evaluar_motor,
        axis=1,
    )

    # --------------------------------------------------------
    # Redondeo
    # --------------------------------------------------------

    df["KW"] = df["KW"].round(2)

    df["CORRIENTE_CALCULADA_A"] = (
        df["CORRIENTE_CALCULADA_A"].round(2)
    )

    df["DESVIACION_CALC_PLACA_PCT"] = (
        df["DESVIACION_CALC_PLACA_PCT"].round(2)
    )

    df["CARGA_CORRIENTE_PCT"] = (
        df["CARGA_CORRIENTE_PCT"].round(2)
    )

    # --------------------------------------------------------
    # Exportar
    # --------------------------------------------------------

    df.to_excel(
        ARCHIVO_SALIDA,
        index=False,
    )

    # --------------------------------------------------------
    # Mostrar resultados
    # --------------------------------------------------------

    print()
    print("ANÁLISIS DE MOTORES")
    print("=" * 70)

    columnas_mostrar = [
        "TAG",
        "DESCRIPCION",
        "HP",
        "CORRIENTE_CALCULADA_A",
        "CORRIENTE_PLACA_A",
        "CORRIENTE_MEDIDA_A",
        "CARGA_CORRIENTE_PCT",
        "ALERTA",
    ]

    print(df[columnas_mostrar].to_string(index=False))

    print()
    print("Archivo generado:")
    print(ARCHIVO_SALIDA)


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    calcular_motores()