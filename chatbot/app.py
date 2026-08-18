"""Interfaz de consola del chatbot."""

from chatbot.claude_chat import ChatbotClaude, ErrorChatbot


def ejecutar() -> None:
    """Inicia una sesión interactiva hasta que el usuario decida salir."""
    print("Chatbot HelpDesk con Claude")
    print("Comandos: 'limpiar' borra el contexto y 'salir' termina la sesión.\n")

    try:
        with ChatbotClaude() as chatbot:
            while True:
                mensaje = input("Usuario: ").strip()
                if mensaje.lower() in {"salir", "exit"}:
                    break
                if mensaje.lower() == "limpiar":
                    chatbot.limpiar_contexto()
                    print("Chatbot: Contexto de la sesión eliminado.\n")
                    continue
                if not mensaje:
                    continue

                respuesta = chatbot.responder(mensaje)
                print(f"Chatbot: {respuesta}\n")
    except (ErrorChatbot, KeyboardInterrupt) as error:
        if isinstance(error, KeyboardInterrupt):
            print("\nSesión finalizada.")
        else:
            print(f"Error: {error}")
