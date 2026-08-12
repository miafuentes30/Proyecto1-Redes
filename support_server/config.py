"""Configuración básica del servidor MCP de soporte técnico."""

PROTOCOL_VERSION = "2025-11-25"
SERVER_NAME = "helpdesk-mcp-server"
SERVER_VERSION = "0.2.0"

TOOLS = [
    {
        "name": "create_ticket",
        "title": "Crear solicitud de soporte",
        "description": "Registra una nueva solicitud de soporte técnico.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "usuario": {"type": "string", "description": "Nombre del usuario."},
                "descripcion": {
                    "type": "string",
                    "description": "Descripción del problema técnico.",
                },
                "prioridad": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                },
            },
            "required": ["usuario", "descripcion"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_ticket",
        "title": "Consultar solicitud",
        "description": "Consulta una solicitud de soporte por su ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "integer", "minimum": 1}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_tickets",
        "title": "Listar solicitudes",
        "description": "Lista todas las solicitudes de soporte existentes.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    {
        "name": "update_ticket_status",
        "title": "Actualizar estado",
        "description": "Actualiza el estado de una solicitud de soporte.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "minimum": 1},
                "estado": {
                    "type": "string",
                    "enum": ["open", "in_progress", "closed"],
                },
            },
            "required": ["id", "estado"],
            "additionalProperties": False,
        },
    },
]
