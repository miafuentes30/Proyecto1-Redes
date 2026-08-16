"""Demostración del cliente MCP local."""

import argparse
import json
import logging

from mcp_client.client import ClienteMcpLocal, ErrorClienteMcp


def ejecutar_demo(mostrar_interacciones: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        with ClienteMcpLocal(mostrar_interacciones=mostrar_interacciones) as cliente:
            herramientas = cliente.listar_herramientas()
            print("Herramientas disponibles:")
            for herramienta in herramientas:
                print(f"- {herramienta['name']}")

            creado = cliente.ejecutar_herramienta(
                "create_ticket",
                {
                    "usuario": "Usuario de demostración",
                    "descripcion": "Prueba del cliente MCP local",
                    "prioridad": "medium",
                },
            )
            ticket = creado["structuredContent"]["ticket"]
            print("\nTicket creado:")
            print(json.dumps(ticket, ensure_ascii=False, indent=2))

            consultado = cliente.ejecutar_herramienta(
                "get_ticket", {"id": ticket["id"]}
            )
            print("\nTicket consultado:")
            print(
                json.dumps(
                    consultado["structuredContent"]["ticket"],
                    ensure_ascii=False,
                    indent=2,
                )
            )
    except ErrorClienteMcp as error:
        logging.error("La demostración no pudo completarse: %s", error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demostración del cliente MCP local")
    parser.add_argument(
        "--mostrar-interacciones",
        action="store_true",
        help="Muestra los mensajes MCP por stderr durante la ejecución.",
    )
    argumentos = parser.parse_args()
    ejecutar_demo(argumentos.mostrar_interacciones)
