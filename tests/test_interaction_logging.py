"""Pruebas del registro de interacciones MCP."""

import tempfile
import unittest
from pathlib import Path

from mcp_client.interaction_logging import RegistroInteraccionesMcp


class RegistroInteraccionesTest(unittest.TestCase):
    def test_registra_datos_y_oculta_secretos(self) -> None:
        with tempfile.TemporaryDirectory() as directorio:
            log_path = Path(directorio) / "interacciones.log"
            registro = RegistroInteraccionesMcp(log_path)
            registro.registrar(
                "servidor-prueba",
                "CLIENT -> SERVER",
                "tools/call",
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {"api_key": "no-debe-aparecer"},
                },
            )
            registro.cerrar()

            contenido = log_path.read_text(encoding="utf-8")

        self.assertIn("CLIENT -> SERVER", contenido)
        self.assertIn("method=tools/call", contenido)
        self.assertIn("id=7", contenido)
        self.assertIn("[REDACTADO]", contenido)
        self.assertNotIn("no-debe-aparecer", contenido)
