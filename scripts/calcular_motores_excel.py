from pathlib import Path

import pandas as pd

from scripts.configuracion import (
    cargar_parametros,
)

from scripts.analisis_motores import (
    procesar_motores,
    generar_resumen,
)

from scripts.reporte_motores import (
    exportar_reporte,
)


# ============================================================
# RUTAS
# ============================================================

RAIZ = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

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
# EJECUCIÓN
# ============================================================

def main():
    """
    Ejecutar análisis completo de motores.
    """

    if not ARCHIVO_ENTRADA.exists():

        raise FileNotFoundError(
            "No existe el archivo:\n"
            f"{ARCHIVO_ENTRADA}"
        )

    # --------------------------------------------------------
    # Parámetros
    # --------------------------------------------------------

    parametros = (
        cargar_parametros()
    )

    # --------------------------------------------------------
    # Leer hojas
    # --------------------------------------------------------

    motores = pd.read_excel(
        ARCHIVO_ENTRADA,
        sheet_name="MOTORES",
    )

    mediciones = pd.read_excel(
        ARCHIVO_ENTRADA,
        sheet_name="MEDICIONES",
    )

    # --------------------------------------------------------
    # Procesar
    # --------------------------------------------------------

    resultados = procesar_motores(
        motores,
        mediciones,
        parametros,
    )

    # --------------------------------------------------------
    # Resumen
    # --------------------------------------------------------

    resumen = generar_resumen(
        resultados,
        parametros,
    )

    # --------------------------------------------------------
    # Exportar
    # --------------------------------------------------------

    exportar_reporte(
        resultados,
        resumen,
        ARCHIVO_SALIDA,
    )

    # --------------------------------------------------------
    # Mostrar resultados
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("ANÁLISIS DE MOTORES TERMINADO")
    print("=" * 80)

    columnas = [
        "TAG",
        "DESCRIPCION",
        "FECHA",
        "CORRIENTE_PROMEDIO_A",
        "CARGA_CORRIENTE_PCT",
        "DESBALANCE_CORRIENTE_PCT",
        "DESBALANCE_VOLTAJE_PCT",
        "DIAGNOSTICO_GENERAL",
    ]

    print()

    print(
        resultados[
            columnas
        ].to_string(
            index=False
        )
    )

    print()
    print("Archivo generado:")
    print(ARCHIVO_SALIDA)


# ============================================================
# EJECUCIÓN DIRECTA
# ============================================================

if __name__ == "__main__":
    main()