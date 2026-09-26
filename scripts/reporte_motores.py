import pandas as pd

from openpyxl import load_workbook

from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side,
)

from openpyxl.utils import (
    get_column_letter,
)


def exportar_reporte(
    df,
    resumen,
    archivo_salida,
):
    """
    Crear reporte Excel y aplicar formato.
    """

    archivo_salida.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:

        with pd.ExcelWriter(
            archivo_salida,
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

        formatear_excel(
            archivo_salida
        )

    except PermissionError as error:

        raise PermissionError(
            "\nNo se puede escribir:\n"
            f"{archivo_salida}\n\n"
            "Cierra el archivo Excel "
            "y vuelve a ejecutar."
        ) from error


def formatear_excel(
    archivo_salida,
):
    """
    Aplicar formato visual al reporte.
    """

    wb = load_workbook(
        archivo_salida
    )

    encabezado_fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78",
    )

    encabezado_font = Font(
        color="FFFFFF",
        bold=True,
    )

    lado = Side(
        style="thin",
        color="BFBFBF",
    )

    borde = Border(
        left=lado,
        right=lado,
        top=lado,
        bottom=lado,
    )

    verde = PatternFill(
        fill_type="solid",
        fgColor="C6EFCE",
    )

    amarillo = PatternFill(
        fill_type="solid",
        fgColor="FFEB9C",
    )

    rojo = PatternFill(
        fill_type="solid",
        fgColor="FFC7CE",
    )

    azul = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    # ========================================================
    # MOTORES
    # ========================================================

    ws = wb["MOTORES"]

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.row_dimensions[1].height = 45

    for celda in ws[1]:

        celda.fill = encabezado_fill
        celda.font = encabezado_font
        celda.border = borde

        celda.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    for fila in ws.iter_rows(
        min_row=2,
    ):

        for celda in fila:

            celda.border = borde

            celda.alignment = Alignment(
                vertical="center",
            )

    encabezados = {
        celda.value: celda.column
        for celda in ws[1]
    }

    # Anchos automáticos
    for numero_columna in range(
        1,
        ws.max_column + 1,
    ):

        letra = get_column_letter(
            numero_columna
        )

        maximo = 0

        for fila in range(
            1,
            ws.max_row + 1,
        ):

            valor = ws.cell(
                row=fila,
                column=numero_columna,
            ).value

            if valor is not None:

                maximo = max(
                    maximo,
                    len(str(valor)),
                )

        ws.column_dimensions[
            letra
        ].width = min(
            max(maximo + 3, 12),
            32,
        )

    if "DESCRIPCION" in encabezados:

        letra = get_column_letter(
            encabezados["DESCRIPCION"]
        )

        ws.column_dimensions[
            letra
        ].width = 28

    if (
        "DIAGNOSTICO_GENERAL"
        in encabezados
    ):

        letra = get_column_letter(
            encabezados[
                "DIAGNOSTICO_GENERAL"
            ]
        )

        ws.column_dimensions[
            letra
        ].width = 42

    # Formato numérico
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

    for nombre in columnas_numericas:

        if nombre not in encabezados:
            continue

        columna = encabezados[
            nombre
        ]

        for fila in range(
            2,
            ws.max_row + 1,
        ):

            ws.cell(
                row=fila,
                column=columna,
            ).number_format = "0.00"

    # Alertas
    columnas_alerta = [
        "ALERTA_CARGA",
        "ALERTA_DESBALANCE_CORRIENTE",
        "ALERTA_DESBALANCE_VOLTAJE",
        "DIAGNOSTICO_GENERAL",
    ]

    for nombre in columnas_alerta:

        if nombre not in encabezados:
            continue

        columna = encabezados[
            nombre
        ]

        for fila in range(
            2,
            ws.max_row + 1,
        ):

            celda = ws.cell(
                row=fila,
                column=columna,
            )

            valor = str(
                celda.value
            )

            if valor == "NORMAL":

                celda.fill = verde

            elif valor == "CARGA ALTA":

                celda.fill = amarillo

            elif valor == "CARGA BAJA":

                celda.fill = azul

            else:

                celda.fill = rojo

            celda.font = Font(
                bold=True
            )

            celda.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

    # ========================================================
    # RESUMEN
    # ========================================================

    ws = wb["RESUMEN"]

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    ws.column_dimensions[
        "A"
    ].width = 45

    ws.column_dimensions[
        "B"
    ].width = 22

    for celda in ws[1]:

        celda.fill = encabezado_fill
        celda.font = encabezado_font
        celda.border = borde

        celda.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    for fila in ws.iter_rows(
        min_row=2,
    ):

        for celda in fila:

            celda.border = borde

    for fila in range(
        2,
        ws.max_row + 1,
    ):

        ws[f"B{fila}"].number_format = (
            "0.00"
        )

    wb.save(
        archivo_salida
    )