"""Pruebas de la implementación básica de JSON-RPC 2.0."""

import unittest

from mcp_client.json_rpc import (
    ErrorValidacionJsonRpc,
    construir_error,
    construir_respuesta,
    construir_solicitud,
    deserializar_mensaje,
    serializar_mensaje,
)


class JsonRpcTest(unittest.TestCase):
    def test_solicitud_valida(self) -> None:
        solicitud = construir_solicitud("ejemplo", id=1, params={})
        texto = serializar_mensaje(solicitud)

        self.assertEqual(deserializar_mensaje(texto), solicitud)

    def test_respuesta_valida(self) -> None:
        respuesta = construir_respuesta(1, {"estado": "correcto"})

        self.assertEqual(respuesta["result"], {"estado": "correcto"})

    def test_error_valido(self) -> None:
        respuesta = construir_error(1, -32601, "Método no encontrado")

        self.assertEqual(respuesta["error"]["code"], -32601)

    def test_json_invalido(self) -> None:
        with self.assertRaises(ErrorValidacionJsonRpc):
            deserializar_mensaje('{"jsonrpc": "2.0",')

    def test_mensaje_incompleto(self) -> None:
        with self.assertRaises(ErrorValidacionJsonRpc):
            deserializar_mensaje('{"jsonrpc": "2.0", "id": 1}')


if __name__ == "__main__":
    unittest.main()
