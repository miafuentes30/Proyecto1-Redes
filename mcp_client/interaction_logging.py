"""Registro seguro de mensajes intercambiados con servidores MCP."""

import json
import logging
import sys
from pathlib import Path


CAMPOS_SENSIBLES = ("api_key", "apikey", "authorization", "token", "secret", "password")


class RegistroInteraccionesMcp:
    """Escribe interacciones MCP en un archivo y, opcionalmente, en stderr."""

    def __init__(self, log_path, mostrar: bool = False) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"mcp.interactions.{id(self)}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        formato = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        archivo = logging.FileHandler(self.log_path, encoding="utf-8")
        archivo.setFormatter(formato)
        self.logger.addHandler(archivo)

        if mostrar:
            consola = logging.StreamHandler(sys.stderr)
            consola.setFormatter(formato)
            self.logger.addHandler(consola)

    def registrar(self, servidor: str, direccion: str, metodo: str, mensaje: dict) -> None:
        seguro = self._redactar(mensaje)
        mensaje_json = json.dumps(seguro, ensure_ascii=False, separators=(",", ":"))
        self.logger.info(
            "server=%s | direction=%s | method=%s | id=%s | message=%s",
            servidor,
            direccion,
            metodo,
            mensaje.get("id", "-"),
            mensaje_json,
        )

    def registrar_error(
        self, servidor: str, direccion: str, metodo: str, id_mensaje, error: str
    ) -> None:
        self.logger.error(
            "server=%s | direction=%s | method=%s | id=%s | error=%s",
            servidor,
            direccion,
            metodo,
            id_mensaje if id_mensaje is not None else "-",
            error,
        )

    def cerrar(self) -> None:
        for handler in list(self.logger.handlers):
            handler.close()
            self.logger.removeHandler(handler)

    @classmethod
    def _redactar(cls, valor):
        if isinstance(valor, dict):
            return {
                clave: (
                    "[REDACTADO]"
                    if cls._es_sensible(clave)
                    else cls._redactar(contenido)
                )
                for clave, contenido in valor.items()
            }
        if isinstance(valor, list):
            return [cls._redactar(elemento) for elemento in valor]
        return valor

    @staticmethod
    def _es_sensible(clave) -> bool:
        nombre = str(clave).lower()
        return any(sensible in nombre for sensible in CAMPOS_SENSIBLES)
