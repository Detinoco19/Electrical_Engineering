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

from scripts.configuracion import cargar_parametros


# ============================================================
# RUTAS DEL PROYECTO
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
# CARGAR CONFIGURACIÓN
# ============================================================

PARAMETROS = cargar_parametros()


def validar_parametros():
    """
    Verificar que el archivo YAML contenga los parámetros
    requeridos para evaluar los motores.
    """

    requeridos = {
        "carga_baja_pct",
        "carga_alta_pct",
        "sobrecarga_pct",
    }

    faltantes = (
        requeridos
        - set(PARAMETROS.keys())
    )

    if faltantes:
        raise ValueError(
            "Faltan parámetros en parametros_motores.yaml: "
            f"{sorted(faltantes)}"
        )

    carga_baja = PARAMETROS["carga_baja_pct"]
    carga_alta = PARAMETROS["carga_alta_pct"]
    sobrecarga = PARAMETROS["sobrecarga_pct"]

    if carga_baja < 0:
        raise ValueError(
            "carga_baja_pct no puede ser negativa."
        )

    if carga_alta <= carga_baja:
        raise ValueError(
            "carga_alta_pct debe ser mayor "
            "que carga_baja_pct."
        )

    if sobrecarga <= carga_alta:
        raise ValueError(
            "sobrecarga_pct debe ser mayor "
            "que carga_alta_pct."
        )


# ============================================================
# EVALUACIÓN DEL MOTOR
# ============================================================

def evaluar_motor(fila):
    """
    Evaluar el motor usando la corriente medida respecto
    a la corriente nominal de placa.

    Los límites se leen desde:
    configuracion/parametros_motores.yaml

    CARGA_CORRIENTE_PCT es un indicador eléctrico basado
    en corriente y no representa directamente la carga
    mecánica real del motor.
    """

    carga = fila["CARGA_CORRIENTE_PCT"]

    carga_baja = PARAMETROS[
        "carga_baja_pct"
    ]

    carga_alta = PARAMETROS[
        "carga_alta_pct"
    ]

    sobrecarga = PARAMETROS[
        "sobrecarga_pct"
    ]

    if carga > sobrecarga:
        return "REVISAR SOBRECARGA"

    if carga > carga_alta:
        return "CARGA ALTA"

    if carga < carga_baja:
        return "CARGA BAJA"

    return "NORMAL"


# ============================================================
# VALIDACIÓN DE DATOS DE ENTRADA
# ============================================================

def validar_datos(df):
    """
    Verificar estructura y valores básicos de motores.xlsx.
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

    faltantes = (
        columnas_requeridas
        - set(df.columns)
    )

    if faltantes:
        raise ValueError(
            "Faltan columnas en motores.xlsx: "
            f"{sorted(faltantes)}"
        )

    columnas_numericas = [
        "HP",
        "VOLTAJE",
        "FP",
        "EFICIENCIA",
        "CORRIENTE_PLACA_A",
        "CORRIENTE_MEDIDA_A",
    ]

    # --------------------------------------------------------
    # Valores vacíos
    # --------------------------------------------------------

    for columna in columnas_numericas:

        if df[columna].isnull().any():
            raise ValueError(
                f"Existen valores vacíos en {columna}"
            )

    # --------------------------------------------------------
    # Verificar tipo numérico
    # --------------------------------------------------------

    for columna in columnas_numericas:

        if not pd.api.types.is_numeric_dtype(
            df[columna]
        ):
            raise ValueError(
                f"La columna {columna} debe ser numérica."
            )

    # --------------------------------------------------------
    # Validaciones técnicas
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
# FORMATO DEL REPORTE EXCEL
# ============================================================

def formatear_excel():
    """
    Aplicar formato al archivo motores_calculados.xlsx.
    """

    wb = load_workbook(
        ARCHIVO_SALIDA
    )

    # --------------------------------------------------------
    # Estilos
    # --------------------------------------------------------

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

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    ws.row_dimensions[1].height = 45

    # --------------------------------------------------------
    # Encabezados
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
    # Celdas
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
    # Ancho de columnas
    # --------------------------------------------------------

    anchos = {
        "A": 12,
        "B": 28,
        "C": 10,
        "D": 12,
        "E": 10,
        "F": 14,
        "G": 20,
        "H": 20,
        "I": 15,
        "J": 12,
        "K": 22,
        "L": 26,
        "M": 22,
        "N": 24,
    }

    for columna, ancho in anchos.items():

        ws.column_dimensions[
            columna
        ].width = ancho

    # --------------------------------------------------------
    # Formato numérico
    # --------------------------------------------------------

    for fila in range(
        2,
        ws.max_row + 1,
    ):

        ws[f"C{fila}"].number_format = "0.00"
        ws[f"D{fila}"].number_format = "0.00"
        ws[f"E{fila}"].number_format = "0.00"
        ws[f"F{fila}"].number_format = "0.00"
        ws[f"G{fila}"].number_format = "0.00"
        ws[f"H{fila}"].number_format = "0.00"
        ws[f"J{fila}"].number_format = "0.00"
        ws[f"K{fila}"].number_format = "0.00"
        ws[f"L{fila}"].number_format = "0.00"
        ws[f"M{fila}"].number_format = "0.00"

    # --------------------------------------------------------
    # Centrado
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
    # Colores según alerta
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

    ws_resumen.column_dimensions[
        "A"
    ].width = 40

    ws_resumen.column_dimensions[
        "B"
    ].width = 20

    # --------------------------------------------------------
    # Encabezados resumen
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
    # Datos resumen
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

    for fila in range(
        2,
        ws_resumen.max_row + 1,
    ):

        ws_resumen[
            f"B{fila}"
        ].number_format = "0.00"

    # ========================================================
    # GUARDAR
    # ========================================================

    wb.save(
        ARCHIVO_SALIDA
    )


# ============================================================
# PROCESAMIENTO PRINCIPAL
# ============================================================

def calcular_motores():
    """
    Leer motores.xlsx, ejecutar cálculos, evaluar motores,
    generar resumen y crear reporte Excel.
    """

    # ========================================================
    # VALIDAR CONFIGURACIÓN
    # ========================================================

    validar_parametros()

    # ========================================================
    # VERIFICAR ARCHIVO DE ENTRADA
    # ========================================================

    if not ARCHIVO_ENTRADA.exists():

        raise FileNotFoundError(
            "No se encontró el archivo:\n"
            f"{ARCHIVO_ENTRADA}"
        )

    # ========================================================
    # CREAR CARPETA RESULTADOS
    # ========================================================

    ARCHIVO_SALIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # LEER EXCEL
    # ========================================================

    df = pd.read_excel(
        ARCHIVO_ENTRADA
    )

    validar_datos(df)

    # ========================================================
    # CÁLCULO DE POTENCIA
    # ========================================================

    df["KW"] = df["HP"].apply(
        hp_a_kw
    )

    # ========================================================
    # CORRIENTE CALCULADA
    # ========================================================

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

    # ========================================================
    # DESVIACIÓN CALCULADA VS PLACA
    # ========================================================

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

    # ========================================================
    # INDICADOR DE CARGA POR CORRIENTE
    # ========================================================

    df[
        "CARGA_CORRIENTE_PCT"
    ] = (
        df["CORRIENTE_MEDIDA_A"]
        / df["CORRIENTE_PLACA_A"]
        * 100
    )

    # ========================================================
    # EVALUACIÓN
    # ========================================================

    df["ALERTA"] = df.apply(
        evaluar_motor,
        axis=1,
    )

    # ========================================================
    # REDONDEO
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
    # RESUMEN
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
                "Límite carga baja %",
                "Límite carga alta %",
                "Límite sobrecarga %",
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

                PARAMETROS[
                    "carga_baja_pct"
                ],

                PARAMETROS[
                    "carga_alta_pct"
                ],

                PARAMETROS[
                    "sobrecarga_pct"
                ],
            ],
        }
    )

    # ========================================================
    # EXPORTAR
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
    # FORMATO
    # ========================================================

    formatear_excel()

    # ========================================================
    # MOSTRAR RESULTADOS
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
        "PARÁMETROS DE ANÁLISIS"
    )

    print(
        "=" * 60
    )

    print(
        f"Carga baja: "
        f"{PARAMETROS['carga_baja_pct']} %"
    )

    print(
        f"Carga alta: "
        f"{PARAMETROS['carga_alta_pct']} %"
    )

    print(
        f"Sobrecarga: "
        f"{PARAMETROS['sobrecarga_pct']} %"
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