import pandas as pd

from scripts.motores import (
    hp_a_kw,
    corriente_motor_trifasico,
    promedio_trifasico,
    desbalance_porcentual,
    fase_mayor,
    fase_menor,
)


# ============================================================
# COLUMNAS REQUERIDAS
# ============================================================

COLUMNAS_MOTORES = {
    "TAG",
    "DESCRIPCION",
    "AREA",
    "FABRICANTE",
    "MODELO",
    "TIPO_EQUIPO",
    "KW_PLACA",
    "HP",
    "VOLTAJE_V",
    "CORRIENTE_PLACA_A",
    "FRECUENCIA_HZ",
    "FP",
    "EFICIENCIA",
    "ESTADO",
}


COLUMNAS_MEDICIONES = {
    "FECHA",
    "TAG",
    "CORRIENTE_L1_A",
    "CORRIENTE_L2_A",
    "CORRIENTE_L3_A",
    "VOLTAJE_L1_L2_V",
    "VOLTAJE_L2_L3_V",
    "VOLTAJE_L3_L1_V",
    "TEMPERATURA_C",
    "AISLAMIENTO_MOHM",
    "ESTADO",
    "OBSERVACIONES",
}


# ============================================================
# VALIDAR PARÁMETROS
# ============================================================

def validar_parametros(parametros):

    requeridos = {
        "carga_baja_pct",
        "carga_alta_pct",
        "sobrecarga_pct",
        "desbalance_corriente_alerta_pct",
        "desbalance_voltaje_alerta_pct",
    }

    faltantes = requeridos - set(parametros)

    if faltantes:
        raise ValueError(
            "Faltan parámetros en YAML: "
            f"{sorted(faltantes)}"
        )

    carga_baja = parametros["carga_baja_pct"]
    carga_alta = parametros["carga_alta_pct"]
    sobrecarga = parametros["sobrecarga_pct"]

    if carga_baja < 0:
        raise ValueError(
            "carga_baja_pct no puede ser negativa."
        )

    if carga_alta <= carga_baja:
        raise ValueError(
            "carga_alta_pct debe ser mayor que carga_baja_pct."
        )

    if sobrecarga <= carga_alta:
        raise ValueError(
            "sobrecarga_pct debe ser mayor que carga_alta_pct."
        )

    if (
        parametros["desbalance_corriente_alerta_pct"]
        <= 0
    ):
        raise ValueError(
            "desbalance_corriente_alerta_pct "
            "debe ser mayor que cero."
        )

    if (
        parametros["desbalance_voltaje_alerta_pct"]
        <= 0
    ):
        raise ValueError(
            "desbalance_voltaje_alerta_pct "
            "debe ser mayor que cero."
        )


# ============================================================
# VALIDAR HOJA MOTORES
# ============================================================

def validar_motores(motores):

    faltantes = (
        COLUMNAS_MOTORES
        - set(motores.columns)
    )

    if faltantes:
        raise ValueError(
            "Faltan columnas en hoja MOTORES: "
            f"{sorted(faltantes)}"
        )

    if motores["TAG"].isnull().any():
        raise ValueError(
            "Existen TAG vacíos en MOTORES."
        )

    if motores["TAG"].duplicated().any():

        duplicados = motores.loc[
            motores["TAG"].duplicated(),
            "TAG",
        ].tolist()

        raise ValueError(
            f"TAG duplicados en MOTORES: {duplicados}"
        )

    columnas_numericas = [
        "KW_PLACA",
        "HP",
        "VOLTAJE_V",
        "CORRIENTE_PLACA_A",
        "FRECUENCIA_HZ",
        "FP",
        "EFICIENCIA",
    ]

    for columna in columnas_numericas:

        if motores[columna].isnull().any():
            raise ValueError(
                f"Hay valores vacíos en MOTORES/{columna}"
            )

        if not pd.api.types.is_numeric_dtype(
            motores[columna]
        ):
            raise ValueError(
                f"MOTORES/{columna} debe ser numérica."
            )

    if (motores["HP"] <= 0).any():
        raise ValueError(
            "HP debe ser mayor que cero."
        )

    if (motores["VOLTAJE_V"] <= 0).any():
        raise ValueError(
            "VOLTAJE_V debe ser mayor que cero."
        )

    if (
        (motores["FP"] <= 0)
        | (motores["FP"] > 1)
    ).any():
        raise ValueError(
            "FP debe estar entre 0 y 1."
        )

    if (
        (motores["EFICIENCIA"] <= 0)
        | (motores["EFICIENCIA"] > 1)
    ).any():
        raise ValueError(
            "EFICIENCIA debe estar entre 0 y 1."
        )

    if (
        motores["CORRIENTE_PLACA_A"] <= 0
    ).any():
        raise ValueError(
            "CORRIENTE_PLACA_A debe ser mayor que cero."
        )


# ============================================================
# VALIDAR HOJA MEDICIONES
# ============================================================

def validar_mediciones(
    mediciones,
    motores,
):

    faltantes = (
        COLUMNAS_MEDICIONES
        - set(mediciones.columns)
    )

    if faltantes:
        raise ValueError(
            "Faltan columnas en hoja MEDICIONES: "
            f"{sorted(faltantes)}"
        )

    if mediciones.empty:
        return

    if mediciones["TAG"].isnull().any():
        raise ValueError(
            "Existen TAG vacíos en MEDICIONES."
        )

    tags_motores = set(
        motores["TAG"]
    )

    tags_mediciones = set(
        mediciones["TAG"]
    )

    desconocidos = (
        tags_mediciones
        - tags_motores
    )

    if desconocidos:
        raise ValueError(
            "Hay TAG en MEDICIONES que no existen "
            "en MOTORES: "
            f"{sorted(desconocidos)}"
        )

    mediciones["FECHA"] = pd.to_datetime(
        mediciones["FECHA"],
        errors="coerce",
        dayfirst=True,
    )

    if mediciones["FECHA"].isnull().any():
        raise ValueError(
            "Hay fechas inválidas en MEDICIONES."
        )

    columnas_numericas = [
        "CORRIENTE_L1_A",
        "CORRIENTE_L2_A",
        "CORRIENTE_L3_A",
        "VOLTAJE_L1_L2_V",
        "VOLTAJE_L2_L3_V",
        "VOLTAJE_L3_L1_V",
    ]

    for columna in columnas_numericas:

        if mediciones[columna].isnull().any():
            raise ValueError(
                f"Hay valores vacíos en MEDICIONES/{columna}"
            )

        if not pd.api.types.is_numeric_dtype(
            mediciones[columna]
        ):
            raise ValueError(
                f"MEDICIONES/{columna} debe ser numérica."
            )

        if (mediciones[columna] <= 0).any():
            raise ValueError(
                f"MEDICIONES/{columna} "
                "debe ser mayor que cero."
            )


# ============================================================
# ÚLTIMA MEDICIÓN
# ============================================================

def obtener_ultima_medicion(
    mediciones,
):

    if mediciones.empty:
        return mediciones.copy()

    datos = mediciones.copy()

    datos["FECHA"] = pd.to_datetime(
        datos["FECHA"],
        errors="coerce",
        dayfirst=True,
    )

    datos = datos.sort_values(
        [
            "TAG",
            "FECHA",
        ]
    )

    ultima = (
        datos
        .groupby(
            "TAG",
            as_index=False,
        )
        .tail(1)
    )

    return ultima


# ============================================================
# EVALUAR CARGA
# ============================================================

def evaluar_carga(
    carga_pct,
    parametros,
):

    if pd.isna(carga_pct):
        return "SIN MEDICION"

    if (
        carga_pct
        > parametros["sobrecarga_pct"]
    ):
        return "REVISAR SOBRECARGA"

    if (
        carga_pct
        > parametros["carga_alta_pct"]
    ):
        return "CARGA ALTA"

    if (
        carga_pct
        < parametros["carga_baja_pct"]
    ):
        return "CARGA BAJA"

    return "NORMAL"


# ============================================================
# EVALUAR DESBALANCE DE CORRIENTE
# ============================================================

def evaluar_desbalance_corriente(
    valor,
    parametros,
):

    if pd.isna(valor):
        return "SIN MEDICION"

    limite = parametros[
        "desbalance_corriente_alerta_pct"
    ]

    if valor > limite:
        return "REVISAR DESBALANCE I"

    return "NORMAL"


# ============================================================
# EVALUAR DESBALANCE DE VOLTAJE
# ============================================================

def evaluar_desbalance_voltaje(
    valor,
    parametros,
):

    if pd.isna(valor):
        return "SIN MEDICION"

    limite = parametros[
        "desbalance_voltaje_alerta_pct"
    ]

    if valor > limite:
        return "REVISAR DESBALANCE V"

    return "NORMAL"


# ============================================================
# DIAGNÓSTICO GENERAL
# ============================================================

def generar_diagnostico(
    fila,
):

    if not fila["TIENE_MEDICION"]:
        return "SIN MEDICION"

    problemas = []

    columnas_alerta = [
        "ALERTA_CARGA",
        "ALERTA_DESBALANCE_CORRIENTE",
        "ALERTA_DESBALANCE_VOLTAJE",
    ]

    for columna in columnas_alerta:

        if fila[columna] != "NORMAL":

            problemas.append(
                fila[columna]
            )

    if not problemas:
        return "NORMAL"

    return " | ".join(
        problemas
    )


# ============================================================
# PROCESAR MOTORES
# ============================================================

def procesar_motores(
    motores,
    mediciones,
    parametros,
):

    validar_parametros(
        parametros
    )

    validar_motores(
        motores
    )

    validar_mediciones(
        mediciones,
        motores,
    )

    # --------------------------------------------------------
    # Copia base de activos
    # --------------------------------------------------------

    activos = motores.copy()

    if "ESTADO" in activos.columns:

        activos = activos.rename(
            columns={
                "ESTADO": "ESTADO_ACTIVO",
            }
        )

    if "OBSERVACIONES" in activos.columns:

        activos = activos.rename(
            columns={
                "OBSERVACIONES":
                "OBSERVACIONES_ACTIVO",
            }
        )

    # --------------------------------------------------------
    # Última medición de cada TAG
    # --------------------------------------------------------

    ultima = obtener_ultima_medicion(
        mediciones
    )

    if "ESTADO" in ultima.columns:

        ultima = ultima.rename(
            columns={
                "ESTADO":
                "ESTADO_MEDICION",
            }
        )

    if "OBSERVACIONES" in ultima.columns:

        ultima = ultima.rename(
            columns={
                "OBSERVACIONES":
                "OBSERVACIONES_MEDICION",
            }
        )

    # --------------------------------------------------------
    # Unir activos + mediciones
    # --------------------------------------------------------

    resultado = activos.merge(
        ultima,
        on="TAG",
        how="left",
    )

    resultado[
        "TIENE_MEDICION"
    ] = resultado["FECHA"].notna()

    # ========================================================
    # POTENCIA
    # ========================================================

    resultado[
        "KW_CALCULADO_HP"
    ] = resultado["HP"].apply(
        hp_a_kw
    )

    # ========================================================
    # CORRIENTE TEÓRICA
    # ========================================================

    resultado[
        "CORRIENTE_CALCULADA_A"
    ] = resultado.apply(
        lambda fila: corriente_motor_trifasico(
            hp=fila["HP"],
            voltaje=fila["VOLTAJE_V"],
            factor_potencia=fila["FP"],
            eficiencia=fila["EFICIENCIA"],
        ),
        axis=1,
    )

    # ========================================================
    # DESVIACIÓN CALCULADA VS PLACA
    # ========================================================

    resultado[
        "DESVIACION_CALC_PLACA_PCT"
    ] = (
        (
            resultado["CORRIENTE_CALCULADA_A"]
            - resultado["CORRIENTE_PLACA_A"]
        )
        / resultado["CORRIENTE_PLACA_A"]
        * 100
    )

    # ========================================================
    # COLUMNAS DE MEDICIÓN
    # ========================================================

    resultado[
        "CORRIENTE_PROMEDIO_A"
    ] = float("nan")

    resultado[
        "DESBALANCE_CORRIENTE_PCT"
    ] = float("nan")

    resultado[
        "FASE_MAYOR_CORRIENTE"
    ] = None

    resultado[
        "FASE_MENOR_CORRIENTE"
    ] = None

    resultado[
        "VOLTAJE_PROMEDIO_V"
    ] = float("nan")

    resultado[
        "DESBALANCE_VOLTAJE_PCT"
    ] = float("nan")

    # --------------------------------------------------------
    # Solo equipos con medición
    # --------------------------------------------------------

    mascara = resultado[
        "TIENE_MEDICION"
    ]

    # Corriente promedio
    resultado.loc[
        mascara,
        "CORRIENTE_PROMEDIO_A",
    ] = resultado[
        mascara
    ].apply(
        lambda fila: promedio_trifasico(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    # Desbalance corriente
    resultado.loc[
        mascara,
        "DESBALANCE_CORRIENTE_PCT",
    ] = resultado[
        mascara
    ].apply(
        lambda fila: desbalance_porcentual(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    # Fase mayor
    resultado.loc[
        mascara,
        "FASE_MAYOR_CORRIENTE",
    ] = resultado[
        mascara
    ].apply(
        lambda fila: fase_mayor(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    # Fase menor
    resultado.loc[
        mascara,
        "FASE_MENOR_CORRIENTE",
    ] = resultado[
        mascara
    ].apply(
        lambda fila: fase_menor(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    # Voltaje promedio
    resultado.loc[
        mascara,
        "VOLTAJE_PROMEDIO_V",
    ] = resultado[
        mascara
    ].apply(
        lambda fila: promedio_trifasico(
            fila["VOLTAJE_L1_L2_V"],
            fila["VOLTAJE_L2_L3_V"],
            fila["VOLTAJE_L3_L1_V"],
        ),
        axis=1,
    )

    # Desbalance voltaje
    resultado.loc[
        mascara,
        "DESBALANCE_VOLTAJE_PCT",
    ] = resultado[
        mascara
    ].apply(
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

    resultado[
        "CARGA_CORRIENTE_PCT"
    ] = (
        resultado["CORRIENTE_PROMEDIO_A"]
        / resultado["CORRIENTE_PLACA_A"]
        * 100
    )

    # ========================================================
    # ALERTAS
    # ========================================================

    resultado[
        "ALERTA_CARGA"
    ] = resultado[
        "CARGA_CORRIENTE_PCT"
    ].apply(
        lambda valor: evaluar_carga(
            valor,
            parametros,
        )
    )

    resultado[
        "ALERTA_DESBALANCE_CORRIENTE"
    ] = resultado[
        "DESBALANCE_CORRIENTE_PCT"
    ].apply(
        lambda valor:
        evaluar_desbalance_corriente(
            valor,
            parametros,
        )
    )

    resultado[
        "ALERTA_DESBALANCE_VOLTAJE"
    ] = resultado[
        "DESBALANCE_VOLTAJE_PCT"
    ].apply(
        lambda valor:
        evaluar_desbalance_voltaje(
            valor,
            parametros,
        )
    )

    # ========================================================
    # DIAGNÓSTICO
    # ========================================================

    resultado[
        "DIAGNOSTICO_GENERAL"
    ] = resultado.apply(
        generar_diagnostico,
        axis=1,
    )

    # ========================================================
    # REDONDEO
    # ========================================================

    columnas_redondear = [
        "KW_CALCULADO_HP",
        "CORRIENTE_CALCULADA_A",
        "DESVIACION_CALC_PLACA_PCT",
        "CORRIENTE_PROMEDIO_A",
        "DESBALANCE_CORRIENTE_PCT",
        "VOLTAJE_PROMEDIO_V",
        "DESBALANCE_VOLTAJE_PCT",
        "CARGA_CORRIENTE_PCT",
    ]

    for columna in columnas_redondear:

        resultado[columna] = (
            resultado[columna]
            .round(2)
        )

    return resultado


# ============================================================
# RESUMEN
# ============================================================

def generar_resumen(
    df,
    parametros,
):

    total = len(df)

    con_medicion = int(
        df["TIENE_MEDICION"].sum()
    )

    sin_medicion = (
        total
        - con_medicion
    )

    resumen = pd.DataFrame(
        {
            "INDICADOR": [
                "Total de motores",
                "Motores con medición",
                "Motores sin medición",
                "Potencia instalada kW",
                "Motores diagnóstico normal",
                "Motores con carga alta",
                "Motores con carga baja",
                "Motores con posible sobrecarga",
                "Motores con desbalance de corriente",
                "Motores con desbalance de voltaje",
                "Mayor desbalance de corriente %",
                "Mayor desbalance de voltaje %",
                "Límite carga baja %",
                "Límite carga alta %",
                "Límite sobrecarga %",
                "Límite desbalance corriente %",
                "Límite desbalance voltaje %",
            ],

            "VALOR": [
                total,
                con_medicion,
                sin_medicion,

                round(
                    df["KW_PLACA"].sum(),
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
                    == "REVISAR DESBALANCE I"
                ).sum(),

                (
                    df[
                        "ALERTA_DESBALANCE_VOLTAJE"
                    ]
                    == "REVISAR DESBALANCE V"
                ).sum(),

                (
                    round(
                        df[
                            "DESBALANCE_CORRIENTE_PCT"
                        ].max(),
                        2,
                    )
                    if con_medicion > 0
                    else 0
                ),

                (
                    round(
                        df[
                            "DESBALANCE_VOLTAJE_PCT"
                        ].max(),
                        2,
                    )
                    if con_medicion > 0
                    else 0
                ),

                parametros[
                    "carga_baja_pct"
                ],

                parametros[
                    "carga_alta_pct"
                ],

                parametros[
                    "sobrecarga_pct"
                ],

                parametros[
                    "desbalance_corriente_alerta_pct"
                ],

                parametros[
                    "desbalance_voltaje_alerta_pct"
                ],
            ],
        }
    )

    return resumen