import argparse

from scripts.calcular_motores_excel import (
    main as ejecutar_motores,
)


# ============================================================
# ENCABEZADO
# ============================================================

def mostrar_encabezado():

    print()
    print("=" * 60)
    print(
        "SISTEMA DE INGENIERÍA ELÉCTRICA"
    )
    print("=" * 60)


# ============================================================
# MÓDULO MOTORES
# ============================================================

def ejecutar_modulo_motores():

    print()
    print(
        "Ejecutando análisis de motores..."
    )
    print()

    ejecutar_motores()


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Herramientas de Ingeniería Eléctrica"
        )
    )

    parser.add_argument(
        "modulo",
        choices=[
            "motores",
        ],
        help=(
            "Módulo que se desea ejecutar."
        ),
    )

    argumentos = (
        parser.parse_args()
    )

    mostrar_encabezado()

    if argumentos.modulo == "motores":

        ejecutar_modulo_motores()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()