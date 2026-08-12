"""Ejecución de las herramientas MCP del sistema HelpDesk."""

import json


class HerramientaNoEncontrada(ValueError):
    """Indica que el servidor no publica la herramienta solicitada."""


class TicketTools:
    """Conecta las llamadas MCP con la lógica de tickets."""

    def __init__(self, ticket_service) -> None:
        self.ticket_service = ticket_service

    def ejecutar(self, nombre: str, argumentos: dict) -> dict:
        if nombre == "create_ticket":
            return self._create_ticket(argumentos)
        if nombre == "get_ticket":
            return self._get_ticket(argumentos)
        if nombre == "list_tickets":
            return self._list_tickets(argumentos)
        if nombre == "update_ticket_status":
            return self._update_ticket_status(argumentos)
        raise HerramientaNoEncontrada(nombre)

    def _create_ticket(self, argumentos: dict) -> dict:
        try:
            self._requerir(argumentos, "usuario", "descripcion")
            ticket = self.ticket_service.crear_ticket(
                usuario=argumentos["usuario"],
                descripcion=argumentos["descripcion"],
                prioridad=argumentos.get("prioridad", "medium"),
            )
            return self._resultado_exitoso({"ticket": ticket})
        except ValueError as error:
            return self._resultado_error(str(error))

    def _get_ticket(self, argumentos: dict) -> dict:
        try:
            self._requerir(argumentos, "id")
            ticket = self.ticket_service.consultar_ticket(argumentos["id"])
            if ticket is None:
                return self._resultado_error("El ticket solicitado no existe.")
            return self._resultado_exitoso({"ticket": ticket})
        except ValueError as error:
            return self._resultado_error(str(error))

    def _list_tickets(self, argumentos: dict) -> dict:
        if argumentos:
            return self._resultado_error("list_tickets no recibe argumentos.")
        tickets = self.ticket_service.listar_tickets()
        return self._resultado_exitoso({"tickets": tickets})

    def _update_ticket_status(self, argumentos: dict) -> dict:
        try:
            self._requerir(argumentos, "id", "estado")
            ticket = self.ticket_service.actualizar_estado(
                argumentos["id"], argumentos["estado"]
            )
            if ticket is None:
                return self._resultado_error("El ticket solicitado no existe.")
            return self._resultado_exitoso({"ticket": ticket})
        except ValueError as error:
            return self._resultado_error(str(error))

    @staticmethod
    def _requerir(argumentos: dict, *campos: str) -> None:
        faltantes = [campo for campo in campos if campo not in argumentos]
        if faltantes:
            raise ValueError(f"Faltan argumentos requeridos: {', '.join(faltantes)}.")

    @staticmethod
    def _resultado_exitoso(datos: dict) -> dict:
        return {
            "content": [
                {"type": "text", "text": json.dumps(datos, ensure_ascii=False)}
            ],
            "structuredContent": datos,
        }

    @staticmethod
    def _resultado_error(mensaje: str) -> dict:
        return {"content": [{"type": "text", "text": mensaje}], "isError": True}
