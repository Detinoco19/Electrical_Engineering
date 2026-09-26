from pathlib import Path

import yaml


RAIZ = Path(__file__).resolve().parent.parent

ARCHIVO_CONFIG = (
    RAIZ
    / "configuracion"
    / "parametros_motores.yaml"
)


def cargar_parametros():
    """
    Cargar parámetros desde archivo YAML.
    """

    if not ARCHIVO_CONFIG.exists():

        raise FileNotFoundError(
            "No existe el archivo de configuración:\n"
            f"{ARCHIVO_CONFIG}"
        )

    with open(
        ARCHIVO_CONFIG,
        "r",
        encoding="utf-8",
    ) as archivo:

        parametros = yaml.safe_load(
            archivo
        )

    if parametros is None:
        raise ValueError(
            "El archivo parametros_motores.yaml está vacío."
        )

    return parametros