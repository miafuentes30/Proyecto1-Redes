"""Prueba integral del cliente y servidor MCP locales."""

import tempfile
import unittest
from pathlib import Path

from mcp_client.client import ClienteMcpLocal


class ClienteMcpLocalTest(unittest.TestCase):
    def test_flujo_completo(self) -> None:
        with tempfile.TemporaryDirectory() as directorio:
            database_path = Path(directorio) / "client_test.db"
            log_path = Path(directorio) / "mcp_test.log"
            cliente = ClienteMcpLocal(
                environment={"HELPDESK_DB_PATH": str(database_path)},
                log_path=log_path,
            )

            with cliente:
                herramientas = cliente.listar_herramientas()
                creado = cliente.ejecutar_herramienta(
                    "create_ticket",
                    {
                        "usuario": "Cliente de prueba",
                        "descripcion": "Prueba integral",
                        "prioridad": "low",
                    },
                )
                ticket_id = creado["structuredContent"]["ticket"]["id"]
                consultado = cliente.ejecutar_herramienta(
                    "get_ticket", {"id": ticket_id}
                )

            nombres = [herramienta["name"] for herramienta in herramientas]
            self.assertIn("create_ticket", nombres)
            self.assertEqual(
                consultado["structuredContent"]["ticket"]["id"], ticket_id
            )
            self.assertIsNone(cliente.proceso)
            contenido_log = log_path.read_text(encoding="utf-8")
            self.assertIn("CLIENT -> SERVER", contenido_log)
            self.assertIn("SERVER -> CLIENT", contenido_log)
            self.assertIn("method=initialize", contenido_log)
            self.assertIn("method=tools/call", contenido_log)


if __name__ == "__main__":
    unittest.main()
