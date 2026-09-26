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
# RUTAS DEL PROYECTO
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
# EJECUCIÓN DEL MÓDULO DE MOTORES
# ============================================================

def main():
    """
    Ejecutar análisis completo de motores.
    """

    # --------------------------------------------------------
    # Verificar archivo de entrada
    # --------------------------------------------------------

    if not ARCHIVO_ENTRADA.exists():
        raise FileNotFoundError(
            "No existe el archivo de entrada:\n"
            f"{ARCHIVO_ENTRADA}"
        )

    # --------------------------------------------------------
    # Cargar parámetros
    # --------------------------------------------------------

    parametros = cargar_parametros()

    # --------------------------------------------------------
    # Leer Excel
    # --------------------------------------------------------

    datos = pd.read_excel(
        ARCHIVO_ENTRADA
    )

    # --------------------------------------------------------
    # Procesar motores
    # --------------------------------------------------------

    resultados = procesar_motores(
        datos,
        parametros,
    )

    # --------------------------------------------------------
    # Generar resumen
    # --------------------------------------------------------

    resumen = generar_resumen(
        resultados,
        parametros,
    )

    # --------------------------------------------------------
    # Exportar reporte
    # --------------------------------------------------------

    exportar_reporte(
        resultados,
        resumen,
        ARCHIVO_SALIDA,
    )

    # --------------------------------------------------------
    # Mostrar resultado en terminal
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("ANÁLISIS DE MOTORES TERMINADO")
    print("=" * 70)

    columnas = [
        "TAG",
        "DESCRIPCION",
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