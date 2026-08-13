"""Pruebas del ciclo inicial del servidor MCP local."""

import unittest

from support_server.server import ServidorMcp


def solicitud_initialize() -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "cliente-prueba", "version": "1.0.0"},
        },
    }


class ServidorMcpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.servidor = ServidorMcp()

    def test_initialize(self) -> None:
        respuesta = self.servidor.procesar_mensaje(solicitud_initialize())

        self.assertEqual(respuesta["id"], 1)
        self.assertEqual(respuesta["result"]["protocolVersion"], "2025-11-25")
        self.assertIn("tools", respuesta["result"]["capabilities"])
        self.assertEqual(
            respuesta["result"]["serverInfo"]["name"], "helpdesk-mcp-server"
        )

    def test_notifications_initialized_no_responde(self) -> None:
        notificacion = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }

        respuesta = self.servidor.procesar_mensaje(notificacion)

        self.assertIsNone(respuesta)
        self.assertTrue(self.servidor.inicializado)

    def test_tools_list(self) -> None:
        solicitud = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

        respuesta = self.servidor.procesar_mensaje(solicitud)

        herramienta = respuesta["result"]["tools"][0]
        self.assertEqual(herramienta["name"], "create_ticket")
        self.assertIn("inputSchema", herramienta)

    def test_metodo_inexistente(self) -> None:
        solicitud = {"jsonrpc": "2.0", "id": 3, "method": "desconocido"}

        respuesta = self.servidor.procesar_mensaje(solicitud)

        self.assertEqual(respuesta["error"]["code"], -32601)

    def test_json_invalido(self) -> None:
        respuesta = self.servidor.procesar_linea('{"jsonrpc":')

        self.assertEqual(respuesta["error"]["code"], -32700)
        self.assertIsNone(respuesta["id"])

    def test_initialize_sin_parametros(self) -> None:
        solicitud = {"jsonrpc": "2.0", "id": 4, "method": "initialize"}

        respuesta = self.servidor.procesar_mensaje(solicitud)

        self.assertEqual(respuesta["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()

