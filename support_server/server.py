"""Servidor MCP mínimo comunicado mediante stdin y stdout."""

import logging
import sys

from mcp_client.json_rpc import (
    ErrorJsonInvalido,
    ErrorValidacionJsonRpc,
    construir_error,
    construir_respuesta,
    deserializar_mensaje,
    serializar_mensaje,
)
from support_server.config import (
    PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    TOOLS,
)
from support_server.ticket_service import TicketService
from support_server.tools import HerramientaNoEncontrada, TicketTools

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class ServidorMcp:
    """Procesa los métodos MCP disponibles en esta fase."""

    def __init__(self, ticket_service=None) -> None:
        self.inicializado = False
        self.ticket_service = ticket_service

    def procesar_linea(self, linea: str):
        """Deserializa una línea y devuelve una respuesta, si corresponde."""
        try:
            mensaje = deserializar_mensaje(linea)
        except ErrorJsonInvalido:
            return construir_error(None, -32700, "Parse error")
        except ErrorValidacionJsonRpc:
            return construir_error(None, -32600, "Invalid Request")

        return self.procesar_mensaje(mensaje)

    def procesar_mensaje(self, mensaje: dict):
        """Dirige un mensaje validado al método correspondiente."""
        method = mensaje["method"]
        id_solicitud = mensaje.get("id")

        if method == "initialize":
            return self._initialize(mensaje)

        if method == "notifications/initialized":
            self.inicializado = True
            logger.info("Cliente MCP inicializado.")
            return None

        if method == "tools/list":
            if "id" not in mensaje:
                return None
            return construir_respuesta(id_solicitud, {"tools": TOOLS})

        if method == "tools/call":
            if "id" not in mensaje:
                return None
            return self._tools_call(mensaje)

        # Las notificaciones JSON-RPC nunca reciben una respuesta.
        if "id" not in mensaje:
            return None

        return construir_error(id_solicitud, -32601, "Method not found")

    def _tools_call(self, mensaje: dict) -> dict:
        params = mensaje.get("params")
        if not isinstance(params, dict) or not isinstance(params.get("name"), str):
            return construir_error(mensaje["id"], -32602, "Invalid params")

        argumentos = params.get("arguments", {})
        if not isinstance(argumentos, dict):
            return construir_error(mensaje["id"], -32602, "Invalid params")

        if self.ticket_service is None:
            self.ticket_service = TicketService()

        try:
            resultado = TicketTools(self.ticket_service).ejecutar(
                params["name"], argumentos
            )
        except HerramientaNoEncontrada:
            return construir_error(
                mensaje["id"], -32602, "Unknown tool", {"name": params["name"]}
            )

        return construir_respuesta(mensaje["id"], resultado)

    def _initialize(self, mensaje: dict) -> dict:
        if "id" not in mensaje:
            return construir_error(None, -32600, "Invalid Request")

        params = mensaje.get("params")
        requeridos = ("protocolVersion", "capabilities", "clientInfo")
        if not isinstance(params, dict) or any(campo not in params for campo in requeridos):
            return construir_error(mensaje["id"], -32602, "Invalid params")

        if not isinstance(params["protocolVersion"], str):
            return construir_error(mensaje["id"], -32602, "Invalid params")
        if not isinstance(params["capabilities"], dict):
            return construir_error(mensaje["id"], -32602, "Invalid params")
        if not self._client_info_valido(params["clientInfo"]):
            return construir_error(mensaje["id"], -32602, "Invalid params")

        resultado = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
                "description": "Servidor MCP local para soporte técnico.",
            },
        }
        return construir_respuesta(mensaje["id"], resultado)

    @staticmethod
    def _client_info_valido(client_info) -> bool:
        return (
            isinstance(client_info, dict)
            and isinstance(client_info.get("name"), str)
            and isinstance(client_info.get("version"), str)
        )


def ejecutar_servidor(entrada=sys.stdin, salida=sys.stdout) -> None:
    """Lee mensajes por stdin y escribe respuestas JSON-RPC por stdout."""
    if hasattr(entrada, "reconfigure"):
        entrada.reconfigure(encoding="utf-8")
    if hasattr(salida, "reconfigure"):
        salida.reconfigure(encoding="utf-8", newline="\n")

    servidor = ServidorMcp()
    logger.info("Servidor MCP iniciado.")

    for linea in entrada:
        if not linea.strip():
            continue

        try:
            respuesta = servidor.procesar_linea(linea)
        except Exception:
            logger.exception("Error interno al procesar un mensaje.")
            respuesta = construir_error(None, -32603, "Internal error")

        if respuesta is not None:
            salida.write(serializar_mensaje(respuesta) + "\n")
            salida.flush()


if __name__ == "__main__":
    ejecutar_servidor()
