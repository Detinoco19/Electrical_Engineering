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
from openpyxl.utils import get_column_letter

from scripts.motores import (
    hp_a_kw,
    corriente_motor_trifasico,
    promedio_trifasico,
    desbalance_porcentual,
    fase_mayor,
    fase_menor,
)

from scripts.configuracion import cargar_parametros


# ============================================================
# RUTAS
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
# CONFIGURACIÓN
# ============================================================

PARAMETROS = cargar_parametros()


# ============================================================
# VALIDAR PARÁMETROS
# ============================================================

def validar_parametros():
    """
    Verificar los parámetros definidos en el archivo YAML.
    """

    requeridos = {
        "carga_baja_pct",
        "carga_alta_pct",
        "sobrecarga_pct",
        "desbalance_corriente_alerta_pct",
        "desbalance_voltaje_alerta_pct",
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

    carga_baja = PARAMETROS[
        "carga_baja_pct"
    ]

    carga_alta = PARAMETROS[
        "carga_alta_pct"
    ]

    sobrecarga = PARAMETROS[
        "sobrecarga_pct"
    ]

    desbalance_i = PARAMETROS[
        "desbalance_corriente_alerta_pct"
    ]

    desbalance_v = PARAMETROS[
        "desbalance_voltaje_alerta_pct"
    ]

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

    if desbalance_i <= 0:
        raise ValueError(
            "desbalance_corriente_alerta_pct "
            "debe ser mayor que cero."
        )

    if desbalance_v <= 0:
        raise ValueError(
            "desbalance_voltaje_alerta_pct "
            "debe ser mayor que cero."
        )


# ============================================================
# VALIDAR DATOS DE ENTRADA
# ============================================================

def validar_datos(df):
    """
    Verificar estructura y valores del archivo motores.xlsx.
    """

    columnas_requeridas = {
        "TAG",
        "DESCRIPCION",
        "HP",
        "VOLTAJE",
        "FP",
        "EFICIENCIA",
        "CORRIENTE_PLACA_A",
        "CORRIENTE_L1_A",
        "CORRIENTE_L2_A",
        "CORRIENTE_L3_A",
        "VOLTAJE_L1_L2_V",
        "VOLTAJE_L2_L3_V",
        "VOLTAJE_L3_L1_V",
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

    # --------------------------------------------------------
    # TAG
    # --------------------------------------------------------

    if df["TAG"].isnull().any():
        raise ValueError(
            "Existen TAG vacíos."
        )

    if df["TAG"].duplicated().any():
        duplicados = (
            df.loc[
                df["TAG"].duplicated(),
                "TAG",
            ]
            .tolist()
        )

        raise ValueError(
            "Existen TAG duplicados: "
            f"{duplicados}"
        )

    # --------------------------------------------------------
    # Columnas numéricas
    # --------------------------------------------------------

    columnas_numericas = [
        "HP",
        "VOLTAJE",
        "FP",
        "EFICIENCIA",
        "CORRIENTE_PLACA_A",
        "CORRIENTE_L1_A",
        "CORRIENTE_L2_A",
        "CORRIENTE_L3_A",
        "VOLTAJE_L1_L2_V",
        "VOLTAJE_L2_L3_V",
        "VOLTAJE_L3_L1_V",
    ]

    for columna in columnas_numericas:

        if df[columna].isnull().any():
            raise ValueError(
                f"Existen valores vacíos en {columna}"
            )

        if not pd.api.types.is_numeric_dtype(
            df[columna]
        ):
            raise ValueError(
                f"La columna {columna} debe ser numérica."
            )

    # --------------------------------------------------------
    # Validaciones básicas
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

    columnas_corriente = [
        "CORRIENTE_L1_A",
        "CORRIENTE_L2_A",
        "CORRIENTE_L3_A",
    ]

    for columna in columnas_corriente:

        if (df[columna] <= 0).any():
            raise ValueError(
                f"{columna} debe ser mayor que cero."
            )

    columnas_voltaje = [
        "VOLTAJE_L1_L2_V",
        "VOLTAJE_L2_L3_V",
        "VOLTAJE_L3_L1_V",
    ]

    for columna in columnas_voltaje:

        if (df[columna] <= 0).any():
            raise ValueError(
                f"{columna} debe ser mayor que cero."
            )


# ============================================================
# EVALUACIÓN DE CARGA
# ============================================================

def evaluar_carga(carga_pct):
    """
    Evaluar corriente promedio respecto a corriente de placa.
    """

    carga_baja = PARAMETROS[
        "carga_baja_pct"
    ]

    carga_alta = PARAMETROS[
        "carga_alta_pct"
    ]

    sobrecarga = PARAMETROS[
        "sobrecarga_pct"
    ]

    if carga_pct > sobrecarga:
        return "REVISAR SOBRECARGA"

    if carga_pct > carga_alta:
        return "CARGA ALTA"

    if carga_pct < carga_baja:
        return "CARGA BAJA"

    return "NORMAL"


# ============================================================
# EVALUACIÓN DE DESBALANCE DE CORRIENTE
# ============================================================

def evaluar_desbalance_corriente(
    desbalance_pct,
):
    """
    Evaluar desbalance de corriente.
    """

    limite = PARAMETROS[
        "desbalance_corriente_alerta_pct"
    ]

    if desbalance_pct > limite:
        return "REVISAR DESBALANCE I"

    return "NORMAL"


# ============================================================
# EVALUACIÓN DE DESBALANCE DE VOLTAJE
# ============================================================

def evaluar_desbalance_voltaje(
    desbalance_pct,
):
    """
    Evaluar desbalance de voltaje.
    """

    limite = PARAMETROS[
        "desbalance_voltaje_alerta_pct"
    ]

    if desbalance_pct > limite:
        return "REVISAR DESBALANCE V"

    return "NORMAL"


# ============================================================
# DIAGNÓSTICO GENERAL
# ============================================================

def generar_diagnostico(fila):
    """
    Combinar las diferentes alertas del motor.
    """

    problemas = []

    if fila["ALERTA_CARGA"] != "NORMAL":
        problemas.append(
            fila["ALERTA_CARGA"]
        )

    if (
        fila[
            "ALERTA_DESBALANCE_CORRIENTE"
        ]
        != "NORMAL"
    ):
        problemas.append(
            fila[
                "ALERTA_DESBALANCE_CORRIENTE"
            ]
        )

    if (
        fila[
            "ALERTA_DESBALANCE_VOLTAJE"
        ]
        != "NORMAL"
    ):
        problemas.append(
            fila[
                "ALERTA_DESBALANCE_VOLTAJE"
            ]
        )

    if not problemas:
        return "NORMAL"

    return " | ".join(
        problemas
    )


# ============================================================
# FORMATO EXCEL
# ============================================================

def formatear_excel():
    """
    Aplicar formato profesional al archivo de resultados.
    """

    wb = load_workbook(
        ARCHIVO_SALIDA
    )

    # ========================================================
    # ESTILOS
    # ========================================================

    relleno_encabezado = PatternFill(
        fill_type="solid",
        fgColor="1F4E78",
    )

    fuente_encabezado = Font(
        color="FFFFFF",
        bold=True,
    )

    borde_lado = Side(
        style="thin",
        color="BFBFBF",
    )

    borde = Border(
        left=borde_lado,
        right=borde_lado,
        top=borde_lado,
        bottom=borde_lado,
    )

    relleno_normal = PatternFill(
        fill_type="solid",
        fgColor="C6EFCE",
    )

    relleno_advertencia = PatternFill(
        fill_type="solid",
        fgColor="FFEB9C",
    )

    relleno_revision = PatternFill(
        fill_type="solid",
        fgColor="FFC7CE",
    )

    relleno_bajo = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    # ========================================================
    # HOJA MOTORES
    # ========================================================

    ws = wb["MOTORES"]

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.row_dimensions[1].height = 45

    # --------------------------------------------------------
    # Encabezado
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
    # Bordes y alineación
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
    # Mapa de encabezados
    # --------------------------------------------------------

    encabezados = {
        celda.value: celda.column
        for celda in ws[1]
    }

    # --------------------------------------------------------
    # Formato numérico
    # --------------------------------------------------------

    columnas_numericas = [
        "HP",
        "VOLTAJE",
        "FP",
        "EFICIENCIA",
        "CORRIENTE_PLACA_A",
        "CORRIENTE_L1_A",
        "CORRIENTE_L2_A",
        "CORRIENTE_L3_A",
        "VOLTAJE_L1_L2_V",
        "VOLTAJE_L2_L3_V",
        "VOLTAJE_L3_L1_V",
        "KW",
        "CORRIENTE_CALCULADA_A",
        "DESVIACION_CALC_PLACA_PCT",
        "CORRIENTE_PROMEDIO_A",
        "DESBALANCE_CORRIENTE_PCT",
        "VOLTAJE_PROMEDIO_V",
        "DESBALANCE_VOLTAJE_PCT",
        "CARGA_CORRIENTE_PCT",
    ]

    for encabezado in columnas_numericas:

        if encabezado not in encabezados:
            continue

        columna = encabezados[
            encabezado
        ]

        for fila in range(
            2,
            ws.max_row + 1,
        ):

            ws.cell(
                row=fila,
                column=columna,
            ).number_format = "0.00"

    # --------------------------------------------------------
    # Ancho automático
    # --------------------------------------------------------

    for columna in range(
        1,
        ws.max_column + 1,
    ):

        letra = get_column_letter(
            columna
        )

        longitud_maxima = 0

        for fila in range(
            1,
            ws.max_row + 1,
        ):

            valor = ws.cell(
                row=fila,
                column=columna,
            ).value

            if valor is None:
                continue

            longitud_maxima = max(
                longitud_maxima,
                len(str(valor)),
            )

        ancho = min(
            max(
                longitud_maxima + 3,
                12,
            ),
            32,
        )

        ws.column_dimensions[
            letra
        ].width = ancho

    # Descripción
    if "DESCRIPCION" in encabezados:

        letra = get_column_letter(
            encabezados["DESCRIPCION"]
        )

        ws.column_dimensions[
            letra
        ].width = 28

    # Diagnóstico
    if "DIAGNOSTICO_GENERAL" in encabezados:

        letra = get_column_letter(
            encabezados[
                "DIAGNOSTICO_GENERAL"
            ]
        )

        ws.column_dimensions[
            letra
        ].width = 42

    # ========================================================
    # COLORES DE ALERTAS
    # ========================================================

    columnas_alertas = [
        "ALERTA_CARGA",
        "ALERTA_DESBALANCE_CORRIENTE",
        "ALERTA_DESBALANCE_VOLTAJE",
    ]

    for encabezado in columnas_alertas:

        if encabezado not in encabezados:
            continue

        columna = encabezados[
            encabezado
        ]

        for fila in range(
            2,
            ws.max_row + 1,
        ):

            celda = ws.cell(
                row=fila,
                column=columna,
            )

            valor = celda.value

            if valor == "NORMAL":

                celda.fill = (
                    relleno_normal
                )

            elif valor == "CARGA ALTA":

                celda.fill = (
                    relleno_advertencia
                )

            elif valor == "CARGA BAJA":

                celda.fill = (
                    relleno_bajo
                )

            else:

                celda.fill = (
                    relleno_revision
                )

            celda.font = Font(
                bold=True
            )

            celda.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

    # --------------------------------------------------------
    # Diagnóstico general
    # --------------------------------------------------------

    if (
        "DIAGNOSTICO_GENERAL"
        in encabezados
    ):

        columna = encabezados[
            "DIAGNOSTICO_GENERAL"
        ]

        for fila in range(
            2,
            ws.max_row + 1,
        ):

            celda = ws.cell(
                row=fila,
                column=columna,
            )

            if celda.value == "NORMAL":

                celda.fill = (
                    relleno_normal
                )

            else:

                celda.fill = (
                    relleno_revision
                )

            celda.font = Font(
                bold=True
            )

            celda.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

    # ========================================================
    # HOJA RESUMEN
    # ========================================================

    ws_resumen = wb["RESUMEN"]

    ws_resumen.freeze_panes = "A2"

    ws_resumen.auto_filter.ref = (
        ws_resumen.dimensions
    )

    ws_resumen.column_dimensions[
        "A"
    ].width = 45

    ws_resumen.column_dimensions[
        "B"
    ].width = 22

    ws_resumen.row_dimensions[
        1
    ].height = 30

    for celda in ws_resumen[1]:

        celda.fill = relleno_encabezado
        celda.font = fuente_encabezado
        celda.border = borde

        celda.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

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

    validar_parametros()

    if not ARCHIVO_ENTRADA.exists():

        raise FileNotFoundError(
            "No existe el archivo:\n"
            f"{ARCHIVO_ENTRADA}"
        )

    ARCHIVO_SALIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_excel(
        ARCHIVO_ENTRADA
    )

    validar_datos(df)

    # ========================================================
    # POTENCIA
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
    # CORRIENTE PROMEDIO
    # ========================================================

    df[
        "CORRIENTE_PROMEDIO_A"
    ] = df.apply(
        lambda fila: promedio_trifasico(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    # ========================================================
    # DESBALANCE DE CORRIENTE
    # ========================================================

    df[
        "DESBALANCE_CORRIENTE_PCT"
    ] = df.apply(
        lambda fila: desbalance_porcentual(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    # ========================================================
    # FASE MAYOR Y MENOR
    # ========================================================

    df[
        "FASE_MAYOR_CORRIENTE"
    ] = df.apply(
        lambda fila: fase_mayor(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    df[
        "FASE_MENOR_CORRIENTE"
    ] = df.apply(
        lambda fila: fase_menor(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    # ========================================================
    # VOLTAJE PROMEDIO
    # ========================================================

    df[
        "VOLTAJE_PROMEDIO_V"
    ] = df.apply(
        lambda fila: promedio_trifasico(
            fila["VOLTAJE_L1_L2_V"],
            fila["VOLTAJE_L2_L3_V"],
            fila["VOLTAJE_L3_L1_V"],
        ),
        axis=1,
    )

    # ========================================================
    # DESBALANCE DE VOLTAJE
    # ========================================================

    df[
        "DESBALANCE_VOLTAJE_PCT"
    ] = df.apply(
        lambda fila: desbalance_porcentual(
            fila["VOLTAJE_L1_L2_V"],
            fila["VOLTAJE_L2_L3_V"],
            fila["VOLTAJE_L3_L1_V"],
        ),
        axis=1,
    )

    # ========================================================
    # CARGA POR CORRIENTE
    # ========================================================

    df[
        "CARGA_CORRIENTE_PCT"
    ] = (
        df["CORRIENTE_PROMEDIO_A"]
        / df["CORRIENTE_PLACA_A"]
        * 100
    )

    # ========================================================
    # ALERTAS
    # ========================================================

    df[
        "ALERTA_CARGA"
    ] = df[
        "CARGA_CORRIENTE_PCT"
    ].apply(
        evaluar_carga
    )

    df[
        "ALERTA_DESBALANCE_CORRIENTE"
    ] = df[
        "DESBALANCE_CORRIENTE_PCT"
    ].apply(
        evaluar_desbalance_corriente
    )

    df[
        "ALERTA_DESBALANCE_VOLTAJE"
    ] = df[
        "DESBALANCE_VOLTAJE_PCT"
    ].apply(
        evaluar_desbalance_voltaje
    )

    # ========================================================
    # DIAGNÓSTICO GENERAL
    # ========================================================

    df[
        "DIAGNOSTICO_GENERAL"
    ] = df.apply(
        generar_diagnostico,
        axis=1,
    )

    # ========================================================
    # REDONDEO
    # ========================================================

    columnas_redondear = [
        "KW",
        "CORRIENTE_CALCULADA_A",
        "DESVIACION_CALC_PLACA_PCT",
        "CORRIENTE_PROMEDIO_A",
        "DESBALANCE_CORRIENTE_PCT",
        "VOLTAJE_PROMEDIO_V",
        "DESBALANCE_VOLTAJE_PCT",
        "CARGA_CORRIENTE_PCT",
    ]

    for columna in columnas_redondear:

        df[columna] = (
            df[columna]
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
                "Motores diagnóstico normal",
                "Motores con carga alta",
                "Motores con carga baja",
                "Motores con posible sobrecarga",
                "Motores con desbalance de corriente",
                "Motores con desbalance de voltaje",
                "Mayor desbalance de corriente %",
                "Mayor desbalance de voltaje %",
                "Carga promedio por corriente %",
                "Límite carga baja %",
                "Límite carga alta %",
                "Límite sobrecarga %",
                "Límite desbalance corriente %",
                "Límite desbalance voltaje %",
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
                    df["DIAGNOSTICO_GENERAL"]
                    == "NORMAL"
                ).sum(),

                (
                    df["ALERTA_CARGA"]
                    == "CARGA ALTA"
                ).sum(),

                (
                    df["ALERTA_CARGA"]
                    == "CARGA BAJA"
                ).sum(),

                (
                    df["ALERTA_CARGA"]
                    == "REVISAR SOBRECARGA"
                ).sum(),

                (
                    df[
                        "ALERTA_DESBALANCE_CORRIENTE"
                    ]
                    != "NORMAL"
                ).sum(),

                (
                    df[
                        "ALERTA_DESBALANCE_VOLTAJE"
                    ]
                    != "NORMAL"
                ).sum(),

                round(
                    df[
                        "DESBALANCE_CORRIENTE_PCT"
                    ].max(),
                    2,
                ),

                round(
                    df[
                        "DESBALANCE_VOLTAJE_PCT"
                    ].max(),
                    2,
                ),

                round(
                    df[
                        "CARGA_CORRIENTE_PCT"
                    ].mean(),
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

                PARAMETROS[
                    "desbalance_corriente_alerta_pct"
                ],

                PARAMETROS[
                    "desbalance_voltaje_alerta_pct"
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

        formatear_excel()

    except PermissionError:

        raise PermissionError(
            "\nNo se puede escribir el archivo:\n"
            f"{ARCHIVO_SALIDA}\n\n"
            "Cierra motores_calculados.xlsx "
            "en Excel y vuelve a ejecutar."
        )

    # ========================================================
    # TERMINAL
    # ========================================================

    print()

    print(
        "ANÁLISIS TRIFÁSICO DE MOTORES"
    )

    print(
        "=" * 110
    )

    columnas_mostrar = [
        "TAG",
        "DESCRIPCION",
        "CORRIENTE_PROMEDIO_A",
        "CARGA_CORRIENTE_PCT",
        "DESBALANCE_CORRIENTE_PCT",
        "DESBALANCE_VOLTAJE_PCT",
        "DIAGNOSTICO_GENERAL",
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