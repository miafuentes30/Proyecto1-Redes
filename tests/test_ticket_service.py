"""Pruebas de persistencia y lógica de tickets."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from database.ticket_repository import TicketRepository
from support_server.ticket_service import TicketService


class TicketServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directorio_temporal = tempfile.TemporaryDirectory()
        database_path = Path(self.directorio_temporal.name) / "tickets_test.db"
        repository = TicketRepository(database_path)
        self.database_path = database_path
        self.service = TicketService(repository)

    def tearDown(self) -> None:
        self.directorio_temporal.cleanup()

    def test_inicializa_base_de_datos(self) -> None:
        with closing(sqlite3.connect(self.database_path)) as conexion:
            tabla = conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'tickets'"
            ).fetchone()

        self.assertEqual(tabla[0], "tickets")

    def test_crear_y_consultar_ticket(self) -> None:
        creado = self.service.crear_ticket(
            "Ana", "La impresora no responde", "high"
        )
        consultado = self.service.consultar_ticket(creado["id"])

        self.assertEqual(consultado["usuario"], "Ana")
        self.assertEqual(consultado["prioridad"], "high")
        self.assertEqual(consultado["estado"], "open")

    def test_listar_tickets(self) -> None:
        self.service.crear_ticket("Ana", "Problema de red")
        self.service.crear_ticket("Luis", "No puede iniciar sesión", "low")

        tickets = self.service.listar_tickets()

        self.assertEqual(len(tickets), 2)
        self.assertEqual(tickets[0]["usuario"], "Ana")

    def test_actualizar_estado(self) -> None:
        ticket = self.service.crear_ticket("Marta", "Equipo sin sonido")

        actualizado = self.service.actualizar_estado(ticket["id"], "closed")

        self.assertEqual(actualizado["estado"], "closed")

    def test_ticket_inexistente(self) -> None:
        self.assertIsNone(self.service.consultar_ticket(999))
        self.assertIsNone(self.service.actualizar_estado(999, "closed"))


if __name__ == "__main__":
    unittest.main()
