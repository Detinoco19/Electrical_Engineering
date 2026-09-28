
import pandas as pd

from scripts.motores import (
    hp_a_kw,
    corriente_motor_trifasico,
    promedio_trifasico,
    desbalance_porcentual,
    fase_mayor,
    fase_menor,
)

COLUMNAS_MOTORES_OBLIGATORIAS = {
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

COLUMNAS_MEDICIONES_OBLIGATORIAS = {
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

COLUMNAS_NUMERICAS_MOTORES_REQUERIDAS = [
    "KW_PLACA",
    "HP",
    "VOLTAJE_V",
    "CORRIENTE_PLACA_A",
    "FRECUENCIA_HZ",
    "FP",
    "EFICIENCIA",
]

COLUMNAS_NUMERICAS_MOTORES_OPCIONALES = [
    "POTENCIA_CV_PLACA",
    "VOLTAJE_PLACA_1_V",
    "CORRIENTE_PLACA_1_A",
    "VOLTAJE_PLACA_2_V",
    "CORRIENTE_PLACA_2_A",
    "RPM_MOTOR",
    "FACTOR_SERVICIO",
    "ELEVACION_TEMP_K",
    "TEMP_AMBIENTE_MIN_C",
    "TEMP_AMBIENTE_MAX_C",
    "ALTITUD_MAX_M",
    "IP_IN",
    "CORRIENTE_FS_1_A",
    "CORRIENTE_FS_2_A",
    "RPM_SALIDA",
    "RELACION_REDUCCION",
    "PAR_SALIDA_NM",
    "VOLUMEN_ACEITE_L",
    "VOLTAJE_FRENO_V",
    "PAR_FRENO_NM",
    "PESO_KG",
]

COLUMNAS_ELECTRICAS_MEDICIONES = [
    "CORRIENTE_L1_A",
    "CORRIENTE_L2_A",
    "CORRIENTE_L3_A",
    "VOLTAJE_L1_L2_V",
    "VOLTAJE_L2_L3_V",
    "VOLTAJE_L3_L1_V",
]

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
        raise ValueError(f"Faltan parámetros en YAML: {sorted(faltantes)}")

    baja = parametros["carga_baja_pct"]
    alta = parametros["carga_alta_pct"]
    sobrecarga = parametros["sobrecarga_pct"]

    if baja < 0:
        raise ValueError("carga_baja_pct no puede ser negativa.")
    if alta <= baja:
        raise ValueError("carga_alta_pct debe ser mayor que carga_baja_pct.")
    if sobrecarga <= alta:
        raise ValueError("sobrecarga_pct debe ser mayor que carga_alta_pct.")
    if parametros["desbalance_corriente_alerta_pct"] <= 0:
        raise ValueError("El límite de desbalance de corriente debe ser mayor que cero.")
    if parametros["desbalance_voltaje_alerta_pct"] <= 0:
        raise ValueError("El límite de desbalance de voltaje debe ser mayor que cero.")

def _limpiar_encabezados(df):
    resultado = df.copy()
    resultado.columns = [str(c).strip() for c in resultado.columns]
    return resultado

def _convertir_numerica(df, columna, permitir_vacio):
    original = df[columna]
    convertido = pd.to_numeric(original, errors="coerce")

    if permitir_vacio:
        no_vacio = original.notna() & original.astype(str).str.strip().ne("")
        invalidos = no_vacio & convertido.isna()
    else:
        invalidos = convertido.isna()

    if invalidos.any():
        filas = (invalidos[invalidos].index + 2).tolist()
        raise ValueError(
            f"Valores no numéricos o inválidos en {columna}. Filas Excel: {filas}"
        )

    df[columna] = convertido

def preparar_motores(motores):
    datos = _limpiar_encabezados(motores)
    faltantes = COLUMNAS_MOTORES_OBLIGATORIAS - set(datos.columns)
    if faltantes:
        raise ValueError(
            f"Faltan columnas en hoja MOTORES: {sorted(faltantes)}"
        )

    if datos["TAG"].isna().any():
        raise ValueError("Existen TAG vacíos en MOTORES.")

    datos["TAG"] = datos["TAG"].astype(str).str.strip()

    if (datos["TAG"] == "").any():
        raise ValueError("Existen TAG vacíos en MOTORES.")

    if datos["TAG"].duplicated().any():
        duplicados = datos.loc[datos["TAG"].duplicated(keep=False), "TAG"].tolist()
        raise ValueError(f"TAG duplicados en MOTORES: {duplicados}")

    for columna in COLUMNAS_NUMERICAS_MOTORES_REQUERIDAS:
        _convertir_numerica(datos, columna, permitir_vacio=False)

    for columna in COLUMNAS_NUMERICAS_MOTORES_OPCIONALES:
        if columna in datos.columns:
            _convertir_numerica(datos, columna, permitir_vacio=True)

    if (datos["KW_PLACA"] <= 0).any():
        raise ValueError("KW_PLACA debe ser mayor que cero.")
    if (datos["HP"] <= 0).any():
        raise ValueError("HP debe ser mayor que cero.")
    if (datos["VOLTAJE_V"] <= 0).any():
        raise ValueError("VOLTAJE_V debe ser mayor que cero.")
    if (datos["CORRIENTE_PLACA_A"] <= 0).any():
        raise ValueError("CORRIENTE_PLACA_A debe ser mayor que cero.")
    if (datos["FRECUENCIA_HZ"] <= 0).any():
        raise ValueError("FRECUENCIA_HZ debe ser mayor que cero.")
    if ((datos["FP"] <= 0) | (datos["FP"] > 1)).any():
        raise ValueError("FP debe estar entre 0 y 1.")
    if ((datos["EFICIENCIA"] <= 0) | (datos["EFICIENCIA"] > 1)).any():
        raise ValueError("EFICIENCIA debe estar entre 0 y 1.")

    if "FECHA_FABRICACION" in datos.columns:
        original = datos["FECHA_FABRICACION"]
        no_vacio = original.notna() & original.astype(str).str.strip().ne("")
        convertido = pd.to_datetime(original, errors="coerce", dayfirst=True)
        invalidos = no_vacio & convertido.isna()
        if invalidos.any():
            filas = (invalidos[invalidos].index + 2).tolist()
            raise ValueError(
                f"FECHA_FABRICACION inválida. Filas Excel: {filas}"
            )
        datos["FECHA_FABRICACION"] = convertido

    return datos

def preparar_mediciones(mediciones, motores):
    datos = _limpiar_encabezados(mediciones)
    faltantes = COLUMNAS_MEDICIONES_OBLIGATORIAS - set(datos.columns)
    if faltantes:
        raise ValueError(
            f"Faltan columnas en hoja MEDICIONES: {sorted(faltantes)}"
        )

    if datos.empty:
        return datos

    if datos["TAG"].isna().any():
        raise ValueError("Existen TAG vacíos en MEDICIONES.")

    datos["TAG"] = datos["TAG"].astype(str).str.strip()

    tags_validos = set(motores["TAG"])
    tags_medidos = set(datos["TAG"])
    desconocidos = tags_medidos - tags_validos
    if desconocidos:
        raise ValueError(
            f"Hay TAG en MEDICIONES que no existen en MOTORES: {sorted(desconocidos)}"
        )

    datos["FECHA"] = pd.to_datetime(
        datos["FECHA"],
        errors="coerce",
        dayfirst=True,
    )
    if datos["FECHA"].isna().any():
        filas = (datos["FECHA"].isna()[datos["FECHA"].isna()].index + 2).tolist()
        raise ValueError(f"Hay fechas inválidas en MEDICIONES. Filas Excel: {filas}")

    for columna in COLUMNAS_ELECTRICAS_MEDICIONES:
        _convertir_numerica(datos, columna, permitir_vacio=False)
        if (datos[columna] <= 0).any():
            raise ValueError(f"MEDICIONES/{columna} debe ser mayor que cero.")

    for columna in ["TEMPERATURA_C", "AISLAMIENTO_MOHM"]:
        _convertir_numerica(datos, columna, permitir_vacio=True)

    return datos

def obtener_ultima_medicion(mediciones):
    if mediciones.empty:
        return mediciones.copy()

    datos = mediciones.copy()
    datos["_ORDEN_ORIGINAL"] = range(len(datos))
    datos = datos.sort_values(["TAG", "FECHA", "_ORDEN_ORIGINAL"])
    ultima = datos.groupby("TAG", as_index=False).tail(1)
    return ultima.drop(columns="_ORDEN_ORIGINAL")

def evaluar_carga(carga_pct, parametros):
    if pd.isna(carga_pct):
        return "SIN MEDICION"
    if carga_pct > parametros["sobrecarga_pct"]:
        return "REVISAR SOBRECARGA"
    if carga_pct > parametros["carga_alta_pct"]:
        return "CARGA ALTA"
    if carga_pct < parametros["carga_baja_pct"]:
        return "CARGA BAJA"
    return "NORMAL"

def evaluar_desbalance_corriente(valor, parametros):
    if pd.isna(valor):
        return "SIN MEDICION"
    if valor > parametros["desbalance_corriente_alerta_pct"]:
        return "REVISAR DESBALANCE I"
    return "NORMAL"

def evaluar_desbalance_voltaje(valor, parametros):
    if pd.isna(valor):
        return "SIN MEDICION"
    if valor > parametros["desbalance_voltaje_alerta_pct"]:
        return "REVISAR DESBALANCE V"
    return "NORMAL"

def generar_diagnostico(fila):
    if not bool(fila["TIENE_MEDICION"]):
        return "SIN MEDICION"

    problemas = []
    for columna in [
        "ALERTA_CARGA",
        "ALERTA_DESBALANCE_CORRIENTE",
        "ALERTA_DESBALANCE_VOLTAJE",
    ]:
        if fila[columna] != "NORMAL":
            problemas.append(fila[columna])

    return "NORMAL" if not problemas else " | ".join(problemas)

def calcular_variables_medicion(resultado, parametros):
    datos = resultado.copy()

    datos["CORRIENTE_PROMEDIO_A"] = datos.apply(
        lambda f: promedio_trifasico(
            f["CORRIENTE_L1_A"],
            f["CORRIENTE_L2_A"],
            f["CORRIENTE_L3_A"],
        ),
        axis=1,
    )
    datos["DESBALANCE_CORRIENTE_PCT"] = datos.apply(
        lambda f: desbalance_porcentual(
            f["CORRIENTE_L1_A"],
            f["CORRIENTE_L2_A"],
            f["CORRIENTE_L3_A"],
        ),
        axis=1,
    )
    datos["FASE_MAYOR_CORRIENTE"] = datos.apply(
        lambda f: fase_mayor(
            f["CORRIENTE_L1_A"],
            f["CORRIENTE_L2_A"],
            f["CORRIENTE_L3_A"],
        ),
        axis=1,
    )
    datos["FASE_MENOR_CORRIENTE"] = datos.apply(
        lambda f: fase_menor(
            f["CORRIENTE_L1_A"],
            f["CORRIENTE_L2_A"],
            f["CORRIENTE_L3_A"],
        ),
        axis=1,
    )
    datos["VOLTAJE_PROMEDIO_V"] = datos.apply(
        lambda f: promedio_trifasico(
            f["VOLTAJE_L1_L2_V"],
            f["VOLTAJE_L2_L3_V"],
            f["VOLTAJE_L3_L1_V"],
        ),
        axis=1,
    )
    datos["DESBALANCE_VOLTAJE_PCT"] = datos.apply(
        lambda f: desbalance_porcentual(
            f["VOLTAJE_L1_L2_V"],
            f["VOLTAJE_L2_L3_V"],
            f["VOLTAJE_L3_L1_V"],
        ),
        axis=1,
    )
    datos["CARGA_CORRIENTE_PCT"] = (
        datos["CORRIENTE_PROMEDIO_A"]
        / datos["CORRIENTE_PLACA_A"]
        * 100
    )
    datos["ALERTA_CARGA"] = datos["CARGA_CORRIENTE_PCT"].apply(
        lambda x: evaluar_carga(x, parametros)
    )
    datos["ALERTA_DESBALANCE_CORRIENTE"] = datos[
        "DESBALANCE_CORRIENTE_PCT"
    ].apply(lambda x: evaluar_desbalance_corriente(x, parametros))
    datos["ALERTA_DESBALANCE_VOLTAJE"] = datos[
        "DESBALANCE_VOLTAJE_PCT"
    ].apply(lambda x: evaluar_desbalance_voltaje(x, parametros))
    datos["DIAGNOSTICO_GENERAL"] = datos.apply(generar_diagnostico, axis=1)

    for columna in [
        "CORRIENTE_PROMEDIO_A",
        "DESBALANCE_CORRIENTE_PCT",
        "VOLTAJE_PROMEDIO_V",
        "DESBALANCE_VOLTAJE_PCT",
        "CARGA_CORRIENTE_PCT",
    ]:
        datos[columna] = datos[columna].round(2)

    return datos

def _calcular_datos_placa(datos):
    resultado = datos.copy()
    resultado["KW_CALCULADO_HP"] = resultado["HP"].apply(hp_a_kw)
    resultado["CORRIENTE_CALCULADA_A"] = resultado.apply(
        lambda f: corriente_motor_trifasico(
            hp=f["HP"],
            voltaje=f["VOLTAJE_V"],
            factor_potencia=f["FP"],
            eficiencia=f["EFICIENCIA"],
        ),
        axis=1,
    )
    resultado["DESVIACION_CALC_PLACA_PCT"] = (
        (
            resultado["CORRIENTE_CALCULADA_A"]
            - resultado["CORRIENTE_PLACA_A"]
        )
        / resultado["CORRIENTE_PLACA_A"]
        * 100
    )
    for columna in [
        "KW_CALCULADO_HP",
        "CORRIENTE_CALCULADA_A",
        "DESVIACION_CALC_PLACA_PCT",
    ]:
        resultado[columna] = resultado[columna].round(2)
    return resultado

def procesar_motores(motores, mediciones, parametros):
    validar_parametros(parametros)
    activos = preparar_motores(motores)
    medidas = preparar_mediciones(mediciones, activos)

    activos = activos.rename(
        columns={
            "ESTADO": "ESTADO_ACTIVO",
            "OBSERVACIONES": "OBSERVACIONES_ACTIVO",
        }
    )

    ultima = obtener_ultima_medicion(medidas).rename(
        columns={
            "ESTADO": "ESTADO_MEDICION",
            "OBSERVACIONES": "OBSERVACIONES_MEDICION",
        }
    )

    resultado = activos.merge(ultima, on="TAG", how="left")
    resultado["TIENE_MEDICION"] = resultado["FECHA"].notna()
    resultado = _calcular_datos_placa(resultado)

    for columna in [
        "CORRIENTE_PROMEDIO_A",
        "DESBALANCE_CORRIENTE_PCT",
        "VOLTAJE_PROMEDIO_V",
        "DESBALANCE_VOLTAJE_PCT",
        "CARGA_CORRIENTE_PCT",
    ]:
        resultado[columna] = float("nan")

    resultado["FASE_MAYOR_CORRIENTE"] = None
    resultado["FASE_MENOR_CORRIENTE"] = None
    resultado["ALERTA_CARGA"] = "SIN MEDICION"
    resultado["ALERTA_DESBALANCE_CORRIENTE"] = "SIN MEDICION"
    resultado["ALERTA_DESBALANCE_VOLTAJE"] = "SIN MEDICION"
    resultado["DIAGNOSTICO_GENERAL"] = "SIN MEDICION"

    mascara = resultado["TIENE_MEDICION"]

    if mascara.any():
        calculado = calcular_variables_medicion(
            resultado.loc[mascara].copy(),
            parametros,
        )
        columnas_calculadas = [
            "CORRIENTE_PROMEDIO_A",
            "DESBALANCE_CORRIENTE_PCT",
            "FASE_MAYOR_CORRIENTE",
            "FASE_MENOR_CORRIENTE",
            "VOLTAJE_PROMEDIO_V",
            "DESBALANCE_VOLTAJE_PCT",
            "CARGA_CORRIENTE_PCT",
            "ALERTA_CARGA",
            "ALERTA_DESBALANCE_CORRIENTE",
            "ALERTA_DESBALANCE_VOLTAJE",
            "DIAGNOSTICO_GENERAL",
        ]
        for columna in columnas_calculadas:
            resultado.loc[mascara, columna] = calculado[columna].values

    return resultado

def procesar_historial(motores, mediciones, parametros):
    validar_parametros(parametros)
    activos = preparar_motores(motores)
    medidas = preparar_mediciones(mediciones, activos)

    if medidas.empty:
        return pd.DataFrame(
            columns=[
                "TAG",
                "FECHA",
                "CORRIENTE_PROMEDIO_A",
                "CARGA_CORRIENTE_PCT",
                "DESBALANCE_CORRIENTE_PCT",
                "DESBALANCE_VOLTAJE_PCT",
                "DIAGNOSTICO_GENERAL",
            ]
        )

    activos = activos.rename(
        columns={
            "ESTADO": "ESTADO_ACTIVO",
            "OBSERVACIONES": "OBSERVACIONES_ACTIVO",
        }
    )
    medidas = medidas.rename(
        columns={
            "ESTADO": "ESTADO_MEDICION",
            "OBSERVACIONES": "OBSERVACIONES_MEDICION",
        }
    )

    resultado = medidas.merge(activos, on="TAG", how="left")
    resultado["TIENE_MEDICION"] = True
    resultado = _calcular_datos_placa(resultado)
    resultado = calcular_variables_medicion(resultado, parametros)
    return resultado.sort_values(["TAG", "FECHA"]).reset_index(drop=True)

def generar_resumen(df, parametros):
    total = len(df)
    con_medicion = int(df["TIENE_MEDICION"].sum())
    sin_medicion = total - con_medicion

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
                round(df["KW_PLACA"].sum(), 2),
                int((df["DIAGNOSTICO_GENERAL"] == "NORMAL").sum()),
                int((df["ALERTA_CARGA"] == "CARGA ALTA").sum()),
                int((df["ALERTA_CARGA"] == "CARGA BAJA").sum()),
                int((df["ALERTA_CARGA"] == "REVISAR SOBRECARGA").sum()),
                int(
                    (
                        df["ALERTA_DESBALANCE_CORRIENTE"]
                        == "REVISAR DESBALANCE I"
                    ).sum()
                ),
                int(
                    (
                        df["ALERTA_DESBALANCE_VOLTAJE"]
                        == "REVISAR DESBALANCE V"
                    ).sum()
                ),
                (
                    round(df["DESBALANCE_CORRIENTE_PCT"].max(), 2)
                    if con_medicion
                    else 0
                ),
                (
                    round(df["DESBALANCE_VOLTAJE_PCT"].max(), 2)
                    if con_medicion
                    else 0
                ),
                parametros["carga_baja_pct"],
                parametros["carga_alta_pct"],
                parametros["sobrecarga_pct"],
                parametros["desbalance_corriente_alerta_pct"],
                parametros["desbalance_voltaje_alerta_pct"],
            ],
        }
    )
    return resumen

def _serie_texto(valor):
    if pd.isna(valor):
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()

def generar_control_calidad(motores, mediciones):
    activos = preparar_motores(motores)
    medidas = preparar_mediciones(mediciones, activos)
    hallazgos = []

    def agregar(nivel, tipo, tag, campo, detalle):
        hallazgos.append(
            {
                "NIVEL": nivel,
                "TIPO": tipo,
                "TAG": tag,
                "CAMPO": campo,
                "DETALLE": detalle,
            }
        )

    for campo in [
        "DESCRIPCION",
        "AREA",
        "FABRICANTE",
        "MODELO",
        "TIPO_EQUIPO",
        "ESTADO",
    ]:
        if campo in activos.columns:
            for _, fila in activos.iterrows():
                valor = fila[campo]
                if pd.isna(valor) or str(valor).strip() == "":
                    agregar(
                        "ADVERTENCIA",
                        "DATO_BASICO_VACIO",
                        fila["TAG"],
                        campo,
                        f"El campo {campo} está vacío.",
                    )

    if "SERIE" in activos.columns:
        series = activos[["TAG", "SERIE"]].copy()
        series["SERIE_NORMALIZADA"] = series["SERIE"].apply(_serie_texto)
        series = series[series["SERIE_NORMALIZADA"] != ""]

        duplicados = series[
            series["SERIE_NORMALIZADA"].duplicated(keep=False)
        ]

        for serie, grupo in duplicados.groupby("SERIE_NORMALIZADA"):
            tags = ", ".join(grupo["TAG"].astype(str))
            for tag in grupo["TAG"]:
                agregar(
                    "ADVERTENCIA",
                    "SERIE_DUPLICADA",
                    tag,
                    "SERIE",
                    f"Número de serie {serie} repetido en: {tags}",
                )

        tags_con_serie = set(series["TAG"])
        for tag in activos.loc[~activos["TAG"].isin(tags_con_serie), "TAG"]:
            agregar(
                "INFORMACION",
                "SERIE_NO_REGISTRADA",
                tag,
                "SERIE",
                "Número de serie todavía no registrado.",
            )

    if "FUENTE_DATOS" in activos.columns:
        for _, fila in activos.iterrows():
            fuente = fila["FUENTE_DATOS"]
            if pd.isna(fuente) or str(fuente).strip() == "":
                agregar(
                    "ADVERTENCIA",
                    "SIN_TRAZABILIDAD",
                    fila["TAG"],
                    "FUENTE_DATOS",
                    "Activo sin fuente de datos identificada.",
                )
            elif str(fuente).strip().upper() == "PLACA REFERENCIA":
                agregar(
                    "INFORMACION",
                    "PLACA_REFERENCIA",
                    fila["TAG"],
                    "FUENTE_DATOS",
                    "Datos basados en una placa utilizada como referencia.",
                )

    columnas_voltaje = {
        "VOLTAJE_V",
        "VOLTAJE_PLACA_1_V",
        "VOLTAJE_PLACA_2_V",
    }
    if columnas_voltaje.issubset(activos.columns):
        for _, fila in activos.iterrows():
            v_operacion = fila["VOLTAJE_V"]
            opciones = [
                fila["VOLTAJE_PLACA_1_V"],
                fila["VOLTAJE_PLACA_2_V"],
            ]
            opciones = [v for v in opciones if pd.notna(v)]
            if opciones and not any(abs(v_operacion - v) <= 0.01 for v in opciones):
                agregar(
                    "ADVERTENCIA",
                    "VOLTAJE_NO_COINCIDE",
                    fila["TAG"],
                    "VOLTAJE_V",
                    f"Voltaje operativo {v_operacion} V no coincide con {opciones}.",
                )

    columnas_corriente = {
        "VOLTAJE_V",
        "CORRIENTE_PLACA_A",
        "VOLTAJE_PLACA_1_V",
        "CORRIENTE_PLACA_1_A",
        "VOLTAJE_PLACA_2_V",
        "CORRIENTE_PLACA_2_A",
    }
    if columnas_corriente.issubset(activos.columns):
        for _, fila in activos.iterrows():
            pares = [
                (fila["VOLTAJE_PLACA_1_V"], fila["CORRIENTE_PLACA_1_A"]),
                (fila["VOLTAJE_PLACA_2_V"], fila["CORRIENTE_PLACA_2_A"]),
            ]
            for v_placa, i_placa in pares:
                if (
                    pd.notna(v_placa)
                    and pd.notna(i_placa)
                    and abs(fila["VOLTAJE_V"] - v_placa) <= 0.01
                ):
                    if abs(fila["CORRIENTE_PLACA_A"] - i_placa) > 0.05:
                        agregar(
                            "ADVERTENCIA",
                            "CORRIENTE_PLACA_INCONSISTENTE",
                            fila["TAG"],
                            "CORRIENTE_PLACA_A",
                            (
                                f"A {fila['VOLTAJE_V']} V se registraron "
                                f"{fila['CORRIENTE_PLACA_A']} A como corriente nominal, "
                                f"pero el par de placa indica {i_placa} A."
                            ),
                        )
                    break

    if not medidas.empty:
        duplicadas = medidas[
            medidas.duplicated(subset=["TAG", "FECHA"], keep=False)
        ]
        for _, fila in duplicadas.iterrows():
            agregar(
                "ADVERTENCIA",
                "MEDICION_DUPLICADA",
                fila["TAG"],
                "FECHA",
                (
                    "Existe más de una medición para el mismo TAG el "
                    f"{fila['FECHA'].strftime('%d/%m/%Y')}. "
                    "Sin una columna HORA, la última medición del día es ambigua."
                ),
            )

    columnas = ["NIVEL", "TIPO", "TAG", "CAMPO", "DETALLE"]
    if not hallazgos:
        return pd.DataFrame(
            [
                {
                    "NIVEL": "OK",
                    "TIPO": "SIN_HALLAZGOS",
                    "TAG": "",
                    "CAMPO": "",
                    "DETALLE": "No se detectaron problemas de calidad de datos.",
                }
            ],
            columns=columnas,
        )

    return pd.DataFrame(hallazgos, columns=columnas)
