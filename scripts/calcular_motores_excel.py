
from pathlib import Path
import pandas as pd

from scripts.configuracion import cargar_parametros
from scripts.analisis_motores import (
    procesar_motores,
    procesar_historial,
    generar_resumen,
    generar_control_calidad,
)
from scripts.reporte_motores import exportar_reporte

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_ENTRADA = RAIZ / "datos" / "motores.xlsx"
ARCHIVO_SALIDA = RAIZ / "resultados" / "motores_calculados.xlsx"


def main():
    if not ARCHIVO_ENTRADA.exists():
        raise FileNotFoundError(
            f"No existe el archivo de entrada:\n{ARCHIVO_ENTRADA}"
        )

    parametros = cargar_parametros()

    libro = pd.ExcelFile(ARCHIVO_ENTRADA)
    hojas_requeridas = {"MOTORES", "MEDICIONES"}
    faltantes = hojas_requeridas - set(libro.sheet_names)

    if faltantes:
        raise ValueError(
            f"Faltan hojas en motores.xlsx: {sorted(faltantes)}"
        )

    motores = pd.read_excel(libro, sheet_name="MOTORES")
    mediciones = pd.read_excel(libro, sheet_name="MEDICIONES")

    resultados = procesar_motores(motores, mediciones, parametros)
    historial = procesar_historial(motores, mediciones, parametros)
    resumen = generar_resumen(resultados, parametros)
    calidad = generar_control_calidad(motores, mediciones)

    exportar_reporte(
        resultados,
        resumen,
        historial,
        calidad,
        ARCHIVO_SALIDA,
    )

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

    vista = resultados[columnas].copy()
    vista["FECHA"] = (
        pd.to_datetime(vista["FECHA"], errors="coerce")
        .dt.strftime("%d/%m/%Y")
    )
    vista = vista.fillna("")

    advertencias = int((calidad["NIVEL"] == "ADVERTENCIA").sum())
    informaciones = int((calidad["NIVEL"] == "INFORMACION").sum())

    print()
    print("=" * 95)
    print("ANÁLISIS DE MOTORES TERMINADO")
    print("=" * 95)
    print()
    print(vista.to_string(index=False))
    print()
    print(f"Motores procesados: {len(resultados)}")
    print(f"Registros históricos procesados: {len(historial)}")
    print(f"Advertencias de calidad: {advertencias}")
    print(f"Informaciones de calidad: {informaciones}")
    print()
    print("Archivo generado:")
    print(ARCHIVO_SALIDA)


if __name__ == "__main__":
    main()
