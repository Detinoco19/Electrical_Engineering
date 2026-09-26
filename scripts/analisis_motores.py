import pandas as pd

from scripts.motores import (
    hp_a_kw,
    corriente_motor_trifasico,
    promedio_trifasico,
    desbalance_porcentual,
    fase_mayor,
    fase_menor,
)


COLUMNAS_REQUERIDAS = {
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


COLUMNAS_NUMERICAS = [
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


def validar_parametros(parametros):
    """
    Validar parámetros definidos en YAML.
    """

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
            "Faltan parámetros: "
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
            "carga_alta_pct debe ser mayor "
            "que carga_baja_pct."
        )

    if sobrecarga <= carga_alta:
        raise ValueError(
            "sobrecarga_pct debe ser mayor "
            "que carga_alta_pct."
        )

    if (
        parametros["desbalance_corriente_alerta_pct"]
        <= 0
    ):
        raise ValueError(
            "El límite de desbalance de corriente "
            "debe ser mayor que cero."
        )

    if (
        parametros["desbalance_voltaje_alerta_pct"]
        <= 0
    ):
        raise ValueError(
            "El límite de desbalance de voltaje "
            "debe ser mayor que cero."
        )


def validar_datos(df):
    """
    Validar estructura del DataFrame de motores.
    """

    faltantes = (
        COLUMNAS_REQUERIDAS
        - set(df.columns)
    )

    if faltantes:
        raise ValueError(
            "Faltan columnas en motores.xlsx: "
            f"{sorted(faltantes)}"
        )

    if df["TAG"].isnull().any():
        raise ValueError(
            "Existen TAG vacíos."
        )

    if df["TAG"].duplicated().any():
        duplicados = df.loc[
            df["TAG"].duplicated(),
            "TAG",
        ].tolist()

        raise ValueError(
            f"TAG duplicados: {duplicados}"
        )

    for columna in COLUMNAS_NUMERICAS:

        if df[columna].isnull().any():
            raise ValueError(
                f"Hay valores vacíos en {columna}"
            )

        if not pd.api.types.is_numeric_dtype(
            df[columna]
        ):
            raise ValueError(
                f"{columna} debe ser numérica."
            )

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

    mediciones = [
        "CORRIENTE_L1_A",
        "CORRIENTE_L2_A",
        "CORRIENTE_L3_A",
        "VOLTAJE_L1_L2_V",
        "VOLTAJE_L2_L3_V",
        "VOLTAJE_L3_L1_V",
    ]

    for columna in mediciones:

        if (df[columna] <= 0).any():
            raise ValueError(
                f"{columna} debe ser mayor que cero."
            )


def evaluar_carga(
    carga_pct,
    parametros,
):
    """
    Evaluar indicador de carga por corriente.
    """

    if carga_pct > parametros["sobrecarga_pct"]:
        return "REVISAR SOBRECARGA"

    if carga_pct > parametros["carga_alta_pct"]:
        return "CARGA ALTA"

    if carga_pct < parametros["carga_baja_pct"]:
        return "CARGA BAJA"

    return "NORMAL"


def evaluar_desbalance_corriente(
    desbalance_pct,
    parametros,
):
    """
    Evaluar desbalance de corriente.
    """

    limite = parametros[
        "desbalance_corriente_alerta_pct"
    ]

    if desbalance_pct > limite:
        return "REVISAR DESBALANCE I"

    return "NORMAL"


def evaluar_desbalance_voltaje(
    desbalance_pct,
    parametros,
):
    """
    Evaluar desbalance de voltaje.
    """

    limite = parametros[
        "desbalance_voltaje_alerta_pct"
    ]

    if desbalance_pct > limite:
        return "REVISAR DESBALANCE V"

    return "NORMAL"


def generar_diagnostico(fila):
    """
    Combinar alertas individuales.
    """

    problemas = []

    alertas = [
        "ALERTA_CARGA",
        "ALERTA_DESBALANCE_CORRIENTE",
        "ALERTA_DESBALANCE_VOLTAJE",
    ]

    for alerta in alertas:

        if fila[alerta] != "NORMAL":
            problemas.append(
                fila[alerta]
            )

    if not problemas:
        return "NORMAL"

    return " | ".join(
        problemas
    )


def procesar_motores(
    df,
    parametros,
):
    """
    Ejecutar todos los cálculos y diagnósticos.
    """

    validar_parametros(
        parametros
    )

    validar_datos(
        df
    )

    resultado = df.copy()

    # Potencia
    resultado["KW"] = (
        resultado["HP"]
        .apply(hp_a_kw)
    )

    # Corriente teórica
    resultado[
        "CORRIENTE_CALCULADA_A"
    ] = resultado.apply(
        lambda fila: corriente_motor_trifasico(
            hp=fila["HP"],
            voltaje=fila["VOLTAJE"],
            factor_potencia=fila["FP"],
            eficiencia=fila["EFICIENCIA"],
        ),
        axis=1,
    )

    # Desviación cálculo / placa
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

    # Corriente promedio
    resultado[
        "CORRIENTE_PROMEDIO_A"
    ] = resultado.apply(
        lambda fila: promedio_trifasico(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    # Desbalance corriente
    resultado[
        "DESBALANCE_CORRIENTE_PCT"
    ] = resultado.apply(
        lambda fila: desbalance_porcentual(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    resultado[
        "FASE_MAYOR_CORRIENTE"
    ] = resultado.apply(
        lambda fila: fase_mayor(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    resultado[
        "FASE_MENOR_CORRIENTE"
    ] = resultado.apply(
        lambda fila: fase_menor(
            fila["CORRIENTE_L1_A"],
            fila["CORRIENTE_L2_A"],
            fila["CORRIENTE_L3_A"],
        ),
        axis=1,
    )

    # Voltaje promedio
    resultado[
        "VOLTAJE_PROMEDIO_V"
    ] = resultado.apply(
        lambda fila: promedio_trifasico(
            fila["VOLTAJE_L1_L2_V"],
            fila["VOLTAJE_L2_L3_V"],
            fila["VOLTAJE_L3_L1_V"],
        ),
        axis=1,
    )

    # Desbalance voltaje
    resultado[
        "DESBALANCE_VOLTAJE_PCT"
    ] = resultado.apply(
        lambda fila: desbalance_porcentual(
            fila["VOLTAJE_L1_L2_V"],
            fila["VOLTAJE_L2_L3_V"],
            fila["VOLTAJE_L3_L1_V"],
        ),
        axis=1,
    )

    # Carga por corriente
    resultado[
        "CARGA_CORRIENTE_PCT"
    ] = (
        resultado["CORRIENTE_PROMEDIO_A"]
        / resultado["CORRIENTE_PLACA_A"]
        * 100
    )

    # Alertas
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
        lambda valor: evaluar_desbalance_corriente(
            valor,
            parametros,
        )
    )

    resultado[
        "ALERTA_DESBALANCE_VOLTAJE"
    ] = resultado[
        "DESBALANCE_VOLTAJE_PCT"
    ].apply(
        lambda valor: evaluar_desbalance_voltaje(
            valor,
            parametros,
        )
    )

    resultado[
        "DIAGNOSTICO_GENERAL"
    ] = resultado.apply(
        generar_diagnostico,
        axis=1,
    )

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

        resultado[columna] = (
            resultado[columna]
            .round(2)
        )

    return resultado


def generar_resumen(
    df,
    parametros,
):
    """
    Generar indicadores generales.
    """

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