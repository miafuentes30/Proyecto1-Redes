"""Integración sencilla entre Claude y nuestro cliente MCP local."""

import os

from anthropic import APIError, Anthropic

from mcp_client.client import ClienteMcpLocal, ErrorClienteMcp


DEFAULT_MODEL = "claude-sonnet-5"
SYSTEM_PROMPT = """Eres un asistente empresarial de soporte técnico.
Responde también preguntas generales de forma clara y breve.
Cuando el usuario quiera crear, consultar, listar o actualizar tickets, utiliza
las herramientas disponibles. Si falta un dato obligatorio, solicítalo antes de
usar la herramienta. No inventes resultados de herramientas."""


class ErrorChatbot(RuntimeError):
    """Error de configuración o comunicación del chatbot."""


class ChatbotClaude:
    """Mantiene la conversación y coordina Claude con las herramientas MCP."""

    def __init__(self, claude_client=None, mcp_client=None, model=None) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if claude_client is None and not api_key:
            raise ErrorChatbot("No se configuró la variable ANTHROPIC_API_KEY.")

        self.claude = claude_client or Anthropic(api_key=api_key)
        self.mcp = mcp_client or ClienteMcpLocal()
        self.model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self.historial = []
        self.herramientas = []

    def iniciar(self) -> None:
        try:
            self.mcp.conectar()
            herramientas_mcp = self.mcp.listar_herramientas()
        except ErrorClienteMcp as error:
            raise ErrorChatbot(f"No fue posible iniciar el cliente MCP: {error}") from error

        self.herramientas = [
            {
                "name": herramienta["name"],
                "description": herramienta.get("description", ""),
                "input_schema": herramienta["inputSchema"],
            }
            for herramienta in herramientas_mcp
        ]

    def responder(self, mensaje_usuario: str) -> str:
        if not isinstance(mensaje_usuario, str) or not mensaje_usuario.strip():
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        self.historial.append({"role": "user", "content": mensaje_usuario.strip()})

        # El límite evita un ciclo infinito si el modelo insiste en usar herramientas.
        for _ in range(5):
            respuesta = self._consultar_claude()
            bloques = [self._bloque_a_dict(bloque) for bloque in respuesta.content]
            self.historial.append({"role": "assistant", "content": bloques})

            usos = [bloque for bloque in bloques if bloque["type"] == "tool_use"]
            if not usos:
                texto = "".join(
                    bloque["text"] for bloque in bloques if bloque["type"] == "text"
                ).strip()
                return texto or "Claude no devolvió una respuesta de texto."

            resultados = [self._ejecutar_tool_use(uso) for uso in usos]
            self.historial.append({"role": "user", "content": resultados})

        raise ErrorChatbot("Se alcanzó el límite de llamadas de herramientas.")

    def cerrar(self) -> None:
        self.mcp.cerrar()

    def limpiar_contexto(self) -> None:
        """Elimina únicamente el historial en memoria de la sesión."""
        self.historial.clear()

    def _consultar_claude(self):
        try:
            return self.claude.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=self.historial,
                tools=self.herramientas,
            )
        except APIError as error:
            raise ErrorChatbot(f"Error de la API de Anthropic: {error}") from error

    def _ejecutar_tool_use(self, uso: dict) -> dict:
        try:
            resultado = self.mcp.ejecutar_herramienta(uso["name"], uso["input"])
            contenido = resultado.get("content", [])
            es_error = resultado.get("isError", False)
        except ErrorClienteMcp as error:
            contenido = str(error)
            es_error = True

        bloque = {
            "type": "tool_result",
            "tool_use_id": uso["id"],
            "content": contenido,
        }
        if es_error:
            bloque["is_error"] = True
        return bloque

    @staticmethod
    def _bloque_a_dict(bloque) -> dict:
        if bloque.type == "text":
            return {"type": "text", "text": bloque.text}
        if bloque.type == "tool_use":
            return {
                "type": "tool_use",
                "id": bloque.id,
                "name": bloque.name,
                "input": bloque.input,
            }
        raise ErrorChatbot(f"Tipo de contenido no soportado: {bloque.type}")

    def __enter__(self):
        try:
            self.iniciar()
            return self
        except Exception:
            self.cerrar()
            raise

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.cerrar()
