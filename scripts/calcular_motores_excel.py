from pathlib import Path

import pandas as pd

from openpyxl import load_workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side,
)

from scripts.motores import (
    hp_a_kw,
    corriente_motor_trifasico,
)


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

ARCHIVO_ENTRADA = (
    RAIZ
    / "datos"
    / "motores.xlsx"
)

ARCHIVO_SALIDA = (
    RAIZ
    / "resultados"
    / "motores_calculados.xlsx"
)


# ============================================================
# EVALUACIÓN DEL MOTOR
# ============================================================

def evaluar_motor(fila):
    """
    Evaluar el motor utilizando la relación entre corriente
    medida y corriente nominal de placa.

    NOTA:
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
# VALIDACIÓN DE DATOS
# ============================================================

def validar_datos(df):
    """
    Verificar estructura y valores básicos del archivo
    datos/motores.xlsx.
    """

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

    columnas_faltantes = (
        columnas_requeridas
        - set(df.columns)
    )

    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas en motores.xlsx: "
            f"{sorted(columnas_faltantes)}"
        )

    # --------------------------------------------------------
    # Columnas numéricas obligatorias
    # --------------------------------------------------------

    columnas_numericas = [
        "HP",
        "VOLTAJE",
        "FP",
        "EFICIENCIA",
        "CORRIENTE_PLACA_A",
        "CORRIENTE_MEDIDA_A",
    ]

    # --------------------------------------------------------
    # Verificar valores vacíos
    # --------------------------------------------------------

    for columna in columnas_numericas:

        if df[columna].isnull().any():
            raise ValueError(
                f"Existen valores vacíos en {columna}"
            )

    # --------------------------------------------------------
    # Verificar datos numéricos
    # --------------------------------------------------------

    for columna in columnas_numericas:

        if not pd.api.types.is_numeric_dtype(
            df[columna]
        ):
            raise ValueError(
                f"La columna {columna} debe ser numérica."
            )

    # --------------------------------------------------------
    # Verificaciones técnicas básicas
    # --------------------------------------------------------

    if (df["HP"] <= 0).any():
        raise ValueError(
            "HP debe ser mayor que cero."
        )

    if (df["VOLTAJE"] <= 0).any():
        raise ValueError(
            "VOLTAJE debe ser mayor que cero."
        )

    if (
        (df["FP"] <= 0)
        | (df["FP"] > 1)
    ).any():
        raise ValueError(
            "FP debe estar entre 0 y 1."
        )

    if (
        (df["EFICIENCIA"] <= 0)
        | (df["EFICIENCIA"] > 1)
    ).any():
        raise ValueError(
            "EFICIENCIA debe estar entre 0 y 1."
        )

    if (
        df["CORRIENTE_PLACA_A"] <= 0
    ).any():
        raise ValueError(
            "CORRIENTE_PLACA_A debe ser mayor que cero."
        )

    if (
        df["CORRIENTE_MEDIDA_A"] < 0
    ).any():
        raise ValueError(
            "CORRIENTE_MEDIDA_A no puede ser negativa."
        )


# ============================================================
# FORMATO DEL ARCHIVO EXCEL
# ============================================================

def formatear_excel():
    """
    Aplicar formato profesional al archivo Excel generado.
    """

    wb = load_workbook(
        ARCHIVO_SALIDA
    )

    # ========================================================
    # ESTILOS GENERALES
    # ========================================================

    relleno_encabezado = PatternFill(
        fill_type="solid",
        fgColor="1F4E78",
    )

    fuente_encabezado = Font(
        color="FFFFFF",
        bold=True,
    )

    lado_borde = Side(
        style="thin",
        color="BFBFBF",
    )

    borde = Border(
        left=lado_borde,
        right=lado_borde,
        top=lado_borde,
        bottom=lado_borde,
    )

    # --------------------------------------------------------
    # Colores de diagnóstico
    # --------------------------------------------------------

    relleno_normal = PatternFill(
        fill_type="solid",
        fgColor="C6EFCE",
    )

    relleno_carga_alta = PatternFill(
        fill_type="solid",
        fgColor="FFEB9C",
    )

    relleno_carga_baja = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    relleno_sobrecarga = PatternFill(
        fill_type="solid",
        fgColor="FFC7CE",
    )

    # ========================================================
    # HOJA MOTORES
    # ========================================================

    ws = wb["MOTORES"]

    # Congelar fila superior
    ws.freeze_panes = "A2"

    # Activar filtro
    ws.auto_filter.ref = ws.dimensions

    # Altura de encabezado
    ws.row_dimensions[1].height = 45

    # --------------------------------------------------------
    # Formatear encabezado
    # --------------------------------------------------------

    for celda in ws[1]:

        celda.fill = relleno_encabezado
        celda.font = fuente_encabezado
        celda.border = borde

        celda.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    # --------------------------------------------------------
    # Formato general de datos
    # --------------------------------------------------------

    for fila in ws.iter_rows(
        min_row=2,
        max_row=ws.max_row,
    ):

        for celda in fila:

            celda.border = borde

            celda.alignment = Alignment(
                vertical="center",
            )

    # --------------------------------------------------------
    # Anchos de columnas
    # --------------------------------------------------------

    anchos = {
        "A": 12,   # TAG
        "B": 28,   # DESCRIPCION
        "C": 10,   # HP
        "D": 12,   # VOLTAJE
        "E": 10,   # FP
        "F": 14,   # EFICIENCIA
        "G": 20,   # CORRIENTE_PLACA_A
        "H": 20,   # CORRIENTE_MEDIDA_A
        "I": 15,   # ESTADO
        "J": 12,   # KW
        "K": 22,   # CORRIENTE_CALCULADA_A
        "L": 26,   # DESVIACION_CALC_PLACA_PCT
        "M": 22,   # CARGA_CORRIENTE_PCT
        "N": 24,   # ALERTA
    }

    for columna, ancho in anchos.items():

        ws.column_dimensions[
            columna
        ].width = ancho

    # --------------------------------------------------------
    # Formatos numéricos
    # --------------------------------------------------------

    for fila in range(
        2,
        ws.max_row + 1,
    ):

        # HP
        ws[f"C{fila}"].number_format = "0.00"

        # Voltaje
        ws[f"D{fila}"].number_format = "0.00"

        # FP
        ws[f"E{fila}"].number_format = "0.00"

        # Eficiencia
        ws[f"F{fila}"].number_format = "0.00"

        # Corriente de placa
        ws[f"G{fila}"].number_format = "0.00"

        # Corriente medida
        ws[f"H{fila}"].number_format = "0.00"

        # kW
        ws[f"J{fila}"].number_format = "0.00"

        # Corriente calculada
        ws[f"K{fila}"].number_format = "0.00"

        # Desviación %
        ws[f"L{fila}"].number_format = "0.00"

        # Carga por corriente %
        ws[f"M{fila}"].number_format = "0.00"

    # --------------------------------------------------------
    # Centrar columnas numéricas
    # --------------------------------------------------------

    columnas_centradas = [
        "A",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
    ]

    for columna in columnas_centradas:

        for fila in range(
            2,
            ws.max_row + 1,
        ):

            ws[
                f"{columna}{fila}"
            ].alignment = Alignment(
                horizontal="center",
                vertical="center",
            )

    # --------------------------------------------------------
    # Colorear alertas
    # --------------------------------------------------------

    for fila in range(
        2,
        ws.max_row + 1,
    ):

        celda_alerta = ws[
            f"N{fila}"
        ]

        alerta = celda_alerta.value

        if alerta == "NORMAL":

            celda_alerta.fill = (
                relleno_normal
            )

        elif alerta == "CARGA ALTA":

            celda_alerta.fill = (
                relleno_carga_alta
            )

        elif alerta == "CARGA BAJA":

            celda_alerta.fill = (
                relleno_carga_baja
            )

        elif alerta == "REVISAR SOBRECARGA":

            celda_alerta.fill = (
                relleno_sobrecarga
            )

        celda_alerta.font = Font(
            bold=True
        )

    # ========================================================
    # HOJA RESUMEN
    # ========================================================

    ws_resumen = wb["RESUMEN"]

    ws_resumen.freeze_panes = "A2"

    ws_resumen.auto_filter.ref = (
        ws_resumen.dimensions
    )

    ws_resumen.row_dimensions[
        1
    ].height = 30

    # --------------------------------------------------------
    # Anchos de columna
    # --------------------------------------------------------

    ws_resumen.column_dimensions[
        "A"
    ].width = 40

    ws_resumen.column_dimensions[
        "B"
    ].width = 20

    # --------------------------------------------------------
    # Encabezados
    # --------------------------------------------------------

    for celda in ws_resumen[1]:

        celda.fill = relleno_encabezado
        celda.font = fuente_encabezado
        celda.border = borde

        celda.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    # --------------------------------------------------------
    # Formato de datos
    # --------------------------------------------------------

    for fila in ws_resumen.iter_rows(
        min_row=2,
        max_row=ws_resumen.max_row,
    ):

        for celda in fila:

            celda.border = borde

            celda.alignment = Alignment(
                vertical="center",
            )

    # Valores del resumen
    for fila in range(
        2,
        ws_resumen.max_row + 1,
    ):

        ws_resumen[
            f"B{fila}"
        ].number_format = "0.00"

    # ========================================================
    # GUARDAR ARCHIVO
    # ========================================================

    wb.save(
        ARCHIVO_SALIDA
    )


# ============================================================
# PROCESAMIENTO PRINCIPAL
# ============================================================

def calcular_motores():
    """
    Leer datos/motores.xlsx, realizar cálculos eléctricos,
    generar diagnóstico, resumen y reporte Excel.
    """

    # ========================================================
    # VERIFICAR ARCHIVO DE ENTRADA
    # ========================================================

    if not ARCHIVO_ENTRADA.exists():

        raise FileNotFoundError(
            "No se encontró el archivo:\n"
            f"{ARCHIVO_ENTRADA}"
        )

    # ========================================================
    # CREAR CARPETA DE RESULTADOS
    # ========================================================

    ARCHIVO_SALIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # LEER DATOS
    # ========================================================

    df = pd.read_excel(
        ARCHIVO_ENTRADA
    )

    # ========================================================
    # VALIDAR DATOS
    # ========================================================

    validar_datos(df)

    # ========================================================
    # CÁLCULOS
    # ========================================================

    # --------------------------------------------------------
    # Potencia HP → kW
    # --------------------------------------------------------

    df["KW"] = df["HP"].apply(
        hp_a_kw
    )

    # --------------------------------------------------------
    # Corriente calculada
    # --------------------------------------------------------

    df[
        "CORRIENTE_CALCULADA_A"
    ] = df.apply(
        lambda fila: corriente_motor_trifasico(
            hp=fila["HP"],
            voltaje=fila["VOLTAJE"],
            factor_potencia=fila["FP"],
            eficiencia=fila["EFICIENCIA"],
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # Diferencia cálculo vs placa
    # --------------------------------------------------------

    df[
        "DESVIACION_CALC_PLACA_PCT"
    ] = (
        (
            df["CORRIENTE_CALCULADA_A"]
            - df["CORRIENTE_PLACA_A"]
        )
        / df["CORRIENTE_PLACA_A"]
        * 100
    )

    # --------------------------------------------------------
    # Indicador de carga basado en corriente
    # --------------------------------------------------------

    df[
        "CARGA_CORRIENTE_PCT"
    ] = (
        df["CORRIENTE_MEDIDA_A"]
        / df["CORRIENTE_PLACA_A"]
        * 100
    )

    # --------------------------------------------------------
    # Diagnóstico
    # --------------------------------------------------------

    df["ALERTA"] = df.apply(
        evaluar_motor,
        axis=1,
    )

    # ========================================================
    # REDONDEAR RESULTADOS
    # ========================================================

    df["KW"] = (
        df["KW"]
        .round(2)
    )

    df[
        "CORRIENTE_CALCULADA_A"
    ] = (
        df[
            "CORRIENTE_CALCULADA_A"
        ]
        .round(2)
    )

    df[
        "DESVIACION_CALC_PLACA_PCT"
    ] = (
        df[
            "DESVIACION_CALC_PLACA_PCT"
        ]
        .round(2)
    )

    df[
        "CARGA_CORRIENTE_PCT"
    ] = (
        df[
            "CARGA_CORRIENTE_PCT"
        ]
        .round(2)
    )

    # ========================================================
    # GENERAR RESUMEN
    # ========================================================

    resumen = pd.DataFrame(
        {
            "INDICADOR": [
                "Total de motores",
                "Potencia instalada HP",
                "Potencia instalada kW",
                "Motores normales",
                "Motores con carga alta",
                "Motores con carga baja",
                "Motores con posible sobrecarga",
                "Corriente calculada total A",
                "Corriente medida total A",
            ],

            "VALOR": [
                len(df),

                round(
                    df["HP"].sum(),
                    2,
                ),

                round(
                    df["KW"].sum(),
                    2,
                ),

                (
                    df["ALERTA"]
                    == "NORMAL"
                ).sum(),

                (
                    df["ALERTA"]
                    == "CARGA ALTA"
                ).sum(),

                (
                    df["ALERTA"]
                    == "CARGA BAJA"
                ).sum(),

                (
                    df["ALERTA"]
                    == "REVISAR SOBRECARGA"
                ).sum(),

                round(
                    df[
                        "CORRIENTE_CALCULADA_A"
                    ].sum(),
                    2,
                ),

                round(
                    df[
                        "CORRIENTE_MEDIDA_A"
                    ].sum(),
                    2,
                ),
            ],
        }
    )

    # ========================================================
    # EXPORTAR A EXCEL
    # ========================================================

    try:

        with pd.ExcelWriter(
            ARCHIVO_SALIDA,
            engine="openpyxl",
        ) as writer:

            df.to_excel(
                writer,
                sheet_name="MOTORES",
                index=False,
            )

            resumen.to_excel(
                writer,
                sheet_name="RESUMEN",
                index=False,
            )

    except PermissionError:

        raise PermissionError(
            "\nNo se puede escribir el archivo:\n"
            f"{ARCHIVO_SALIDA}\n\n"
            "Cierra motores_calculados.xlsx en Excel "
            "y vuelve a ejecutar el programa."
        )

    # ========================================================
    # APLICAR FORMATO PROFESIONAL
    # ========================================================

    formatear_excel()

    # ========================================================
    # MOSTRAR RESULTADOS EN TERMINAL
    # ========================================================

    print()

    print(
        "ANÁLISIS DE MOTORES"
    )

    print(
        "=" * 100
    )

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

    print(
        df[
            columnas_mostrar
        ].to_string(
            index=False
        )
    )

    print()

    print(
        "RESUMEN"
    )

    print(
        "=" * 60
    )

    print(
        resumen.to_string(
            index=False
        )
    )

    print()

    print(
        "Archivo generado:"
    )

    print(
        ARCHIVO_SALIDA
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    calcular_motores()