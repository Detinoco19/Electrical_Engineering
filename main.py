import argparse

from scripts.calcular_motores_excel import (
    main as ejecutar_motores,
)


def mostrar_encabezado():
    print()
    print("=" * 60)
    print("SISTEMA DE INGENIERÍA ELÉCTRICA")
    print("=" * 60)


def ejecutar_modulo_motores():
    """
    Ejecutar análisis completo de motores.
    """

    print()
    print("Ejecutando análisis de motores...")
    print()

    ejecutar_motores()


def main():
    """
    Punto de entrada principal del sistema.
    """

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
        help="Módulo que se desea ejecutar.",
    )

    argumentos = parser.parse_args()

    mostrar_encabezado()

    if argumentos.modulo == "motores":
        ejecutar_modulo_motores()


if __name__ == "__main__":
    main()