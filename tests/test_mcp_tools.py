"""Pruebas de las herramientas MCP conectadas a SQLite."""

import tempfile
import unittest
from pathlib import Path

from database.ticket_repository import TicketRepository
from support_server.server import ServidorMcp
from support_server.ticket_service import TicketService


class HerramientasMcpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directorio_temporal = tempfile.TemporaryDirectory()
        database_path = Path(self.directorio_temporal.name) / "mcp_tools_test.db"
        service = TicketService(TicketRepository(database_path))
        self.servidor = ServidorMcp(service)

    def tearDown(self) -> None:
        self.directorio_temporal.cleanup()

    def llamar(self, nombre: str, argumentos=None, id_solicitud=1) -> dict:
        params = {"name": nombre}
        if argumentos is not None:
            params["arguments"] = argumentos
        return self.servidor.procesar_mensaje(
            {
                "jsonrpc": "2.0",
                "id": id_solicitud,
                "method": "tools/call",
                "params": params,
            }
        )

    def test_tools_list_devuelve_cuatro_herramientas(self) -> None:
        respuesta = self.servidor.procesar_mensaje(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        )

        nombres = [tool["name"] for tool in respuesta["result"]["tools"]]
        self.assertEqual(
            nombres,
            ["create_ticket", "get_ticket", "list_tickets", "update_ticket_status"],
        )

    def test_create_y_get_ticket(self) -> None:
        creado = self.llamar(
            "create_ticket",
            {"usuario": "Ana", "descripcion": "Sin conexión", "prioridad": "high"},
        )
        ticket_id = creado["result"]["structuredContent"]["ticket"]["id"]

        consultado = self.llamar("get_ticket", {"id": ticket_id}, id_solicitud=2)

        self.assertEqual(
            consultado["result"]["structuredContent"]["ticket"]["usuario"], "Ana"
        )

    def test_list_y_update_ticket(self) -> None:
        creado = self.llamar(
            "create_ticket", {"usuario": "Luis", "descripcion": "Equipo lento"}
        )
        ticket_id = creado["result"]["structuredContent"]["ticket"]["id"]

        actualizado = self.llamar(
            "update_ticket_status", {"id": ticket_id, "estado": "closed"}
        )
        listado = self.llamar("list_tickets", {})

        self.assertEqual(
            actualizado["result"]["structuredContent"]["ticket"]["estado"],
            "closed",
        )
        self.assertEqual(len(listado["result"]["structuredContent"]["tickets"]), 1)

    def test_herramienta_inexistente(self) -> None:
        respuesta = self.llamar("delete_ticket", {})

        self.assertEqual(respuesta["error"]["code"], -32602)

    def test_argumentos_faltantes(self) -> None:
        respuesta = self.llamar("create_ticket", {"usuario": "Ana"})

        self.assertTrue(respuesta["result"]["isError"])

    def test_prioridad_y_estado_invalidos(self) -> None:
        prioridad = self.llamar(
            "create_ticket",
            {"usuario": "Ana", "descripcion": "Problema", "prioridad": "urgent"},
        )
        estado = self.llamar(
            "update_ticket_status", {"id": 1, "estado": "unknown"}
        )

        self.assertTrue(prioridad["result"]["isError"])
        self.assertTrue(estado["result"]["isError"])

    def test_ticket_inexistente(self) -> None:
        respuesta = self.llamar("get_ticket", {"id": 999})

        self.assertTrue(respuesta["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
