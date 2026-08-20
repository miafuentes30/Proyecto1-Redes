"""Pruebas del chatbot sin realizar llamadas reales a Anthropic."""

import copy
import unittest
from types import SimpleNamespace

from chatbot.claude_chat import ChatbotClaude


class ClaudeFalso:
    def __init__(self, respuestas) -> None:
        self.respuestas = list(respuestas)
        self.solicitudes = []
        self.messages = self

    def create(self, **kwargs):
        self.solicitudes.append(copy.deepcopy(kwargs))
        return self.respuestas.pop(0)


class McpFalso:
    def __init__(self) -> None:
        self.llamadas = []

    def conectar(self) -> None:
        pass

    def listar_herramientas(self) -> list[dict]:
        return [
            {
                "name": "create_ticket",
                "description": "Crea un ticket.",
                "inputSchema": {"type": "object"},
            }
        ]

    def ejecutar_herramienta(self, nombre, argumentos) -> dict:
        self.llamadas.append((nombre, argumentos))
        return {
            "content": [{"type": "text", "text": "Ticket 1 creado"}],
            "structuredContent": {"ticket": {"id": 1}},
        }

    def cerrar(self) -> None:
        pass


def respuesta(*bloques):
    return SimpleNamespace(content=list(bloques))


class ChatbotClaudeTest(unittest.TestCase):
    def test_mantiene_contexto_entre_preguntas_generales(self) -> None:
        claude = ClaudeFalso(
            [
                respuesta(
                    SimpleNamespace(type="text", text="Alan Turing fue un matemático.")
                ),
                respuesta(SimpleNamespace(type="text", text="Nació en 1912.")),
            ]
        )
        chatbot = ChatbotClaude(claude_client=claude, mcp_client=McpFalso())
        chatbot.iniciar()

        chatbot.responder("¿Quién fue Alan Turing?")
        texto = chatbot.responder("¿Cuándo nació?")

        self.assertEqual(texto, "Nació en 1912.")
        mensajes_segundo_turno = claude.solicitudes[1]["messages"]
        self.assertEqual(len(mensajes_segundo_turno), 3)
        self.assertEqual(mensajes_segundo_turno[0]["content"], "¿Quién fue Alan Turing?")
        self.assertEqual(mensajes_segundo_turno[2]["content"], "¿Cuándo nació?")

    def test_ejecuta_herramienta_y_devuelve_respuesta_final(self) -> None:
        uso = SimpleNamespace(
            type="tool_use",
            id="toolu_1",
            name="create_ticket",
            input={"usuario": "Ana", "descripcion": "Sin Internet"},
        )
        claude = ClaudeFalso(
            [
                respuesta(uso),
                respuesta(SimpleNamespace(type="text", text="Ticket 1 creado.")),
            ]
        )
        mcp = McpFalso()
        chatbot = ChatbotClaude(claude_client=claude, mcp_client=mcp)
        chatbot.iniciar()

        texto = chatbot.responder("Reporta que no tengo Internet")

        self.assertEqual(texto, "Ticket 1 creado.")
        self.assertEqual(mcp.llamadas[0][0], "create_ticket")
        self.assertEqual(chatbot.historial[2]["content"][0]["type"], "tool_result")

    def test_mantiene_contexto_despues_de_crear_ticket(self) -> None:
        uso = SimpleNamespace(
            type="tool_use",
            id="toolu_2",
            name="create_ticket",
            input={"usuario": "Ana", "descripcion": "Sin Internet"},
        )
        claude = ClaudeFalso(
            [
                respuesta(uso),
                respuesta(SimpleNamespace(type="text", text="Ticket creado.")),
                respuesta(
                    SimpleNamespace(
                        type="text", text="El problema era que no tenía Internet."
                    )
                ),
            ]
        )
        chatbot = ChatbotClaude(claude_client=claude, mcp_client=McpFalso())
        chatbot.iniciar()

        chatbot.responder("Crea un ticket porque mi computadora no tiene Internet.")
        texto = chatbot.responder("¿Cuál era el problema que te indiqué?")

        self.assertIn("no tenía Internet", texto)
        mensajes = claude.solicitudes[2]["messages"]
        self.assertEqual(mensajes[1]["content"][0]["type"], "tool_use")
        self.assertEqual(mensajes[2]["content"][0]["type"], "tool_result")
        self.assertEqual(
            mensajes[-1]["content"], "¿Cuál era el problema que te indiqué?"
        )

    def test_limpia_contexto(self) -> None:
        claude = ClaudeFalso(
            [respuesta(SimpleNamespace(type="text", text="Respuesta."))]
        )
        chatbot = ChatbotClaude(claude_client=claude, mcp_client=McpFalso())
        chatbot.iniciar()
        chatbot.responder("Mensaje anterior")

        chatbot.limpiar_contexto()

        self.assertEqual(chatbot.historial, [])


if __name__ == "__main__":
    unittest.main()
