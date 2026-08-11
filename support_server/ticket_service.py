"""Reglas básicas para administrar solicitudes de soporte."""

from datetime import datetime, timezone

from database.ticket_repository import TicketRepository


PRIORIDADES_VALIDAS = {"low", "medium", "high"}
ESTADOS_VALIDOS = {"open", "in_progress", "closed"}


class TicketService:
    """Valida los datos y coordina el acceso a los tickets."""

    def __init__(self, repository=None) -> None:
        self.repository = repository or TicketRepository()

    def crear_ticket(
        self, usuario: str, descripcion: str, prioridad: str = "medium"
    ) -> dict:
        usuario = self._texto_requerido(usuario, "usuario")
        descripcion = self._texto_requerido(descripcion, "descripción")
        prioridad = self._prioridad_valida(prioridad)
        fecha_creacion = datetime.now(timezone.utc).isoformat(timespec="seconds")

        return self.repository.crear(
            usuario=usuario,
            descripcion=descripcion,
            prioridad=prioridad,
            estado="open",
            fecha_creacion=fecha_creacion,
        )

    def consultar_ticket(self, ticket_id: int):
        return self.repository.obtener_por_id(self._id_valido(ticket_id))

    def listar_tickets(self) -> list[dict]:
        return self.repository.listar()

    def actualizar_estado(self, ticket_id: int, estado: str):
        ticket_id = self._id_valido(ticket_id)
        if estado not in ESTADOS_VALIDOS:
            raise ValueError("El estado debe ser open, in_progress o closed.")
        return self.repository.actualizar_estado(ticket_id, estado)

    @staticmethod
    def _texto_requerido(valor, nombre: str) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"El campo {nombre} es obligatorio.")
        return valor.strip()

    @staticmethod
    def _prioridad_valida(prioridad: str) -> str:
        if prioridad not in PRIORIDADES_VALIDAS:
            raise ValueError("La prioridad debe ser low, medium o high.")
        return prioridad

    @staticmethod
    def _id_valido(ticket_id: int) -> int:
        if isinstance(ticket_id, bool) or not isinstance(ticket_id, int) or ticket_id < 1:
            raise ValueError("El ID del ticket debe ser un entero positivo.")
        return ticket_id
