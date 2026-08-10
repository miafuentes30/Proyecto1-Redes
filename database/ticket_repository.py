"""Acceso SQLite para las solicitudes de soporte técnico."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


DEFAULT_DATABASE_PATH = Path(
    os.environ.get(
        "HELPDESK_DB_PATH", Path(__file__).resolve().parent / "helpdesk.db"
    )
)


class TicketRepository:
    """Guarda y consulta tickets sin contener reglas del protocolo MCP."""

    def __init__(self, database_path=DEFAULT_DATABASE_PATH) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.inicializar()

    def _conectar(self) -> sqlite3.Connection:
        conexion = sqlite3.connect(self.database_path)
        conexion.row_factory = sqlite3.Row
        return conexion

    @contextmanager
    def _conexion(self):
        conexion = self._conectar()
        try:
            with conexion:
                yield conexion
        finally:
            conexion.close()

    def inicializar(self) -> None:
        """Crea la tabla de tickets cuando todavía no existe."""
        with self._conexion() as conexion:
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    prioridad TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    fecha_creacion TEXT NOT NULL
                )
                """
            )

    def crear(
        self,
        usuario: str,
        descripcion: str,
        prioridad: str,
        estado: str,
        fecha_creacion: str,
    ) -> dict:
        with self._conexion() as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO tickets
                    (usuario, descripcion, prioridad, estado, fecha_creacion)
                VALUES (?, ?, ?, ?, ?)
                """,
                (usuario, descripcion, prioridad, estado, fecha_creacion),
            )
            ticket_id = cursor.lastrowid

        return self.obtener_por_id(ticket_id)

    def obtener_por_id(self, ticket_id: int):
        with self._conexion() as conexion:
            fila = conexion.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()

        return dict(fila) if fila else None

    def listar(self) -> list[dict]:
        with self._conexion() as conexion:
            filas = conexion.execute("SELECT * FROM tickets ORDER BY id").fetchall()

        return [dict(fila) for fila in filas]

    def actualizar_estado(self, ticket_id: int, estado: str):
        with self._conexion() as conexion:
            cursor = conexion.execute(
                "UPDATE tickets SET estado = ? WHERE id = ?",
                (estado, ticket_id),
            )

        if cursor.rowcount == 0:
            return None
        return self.obtener_por_id(ticket_id)
