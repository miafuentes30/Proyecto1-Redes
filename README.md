# Proyecto 1 - Redes

## Servidor MCP local de mesa de ayuda

Este proyecto implementa un servidor MCP local para un sistema básico de soporte técnico empresarial.

El protocolo MCP está implementado manualmente mediante JSON-RPC 2.0; utiliza la versión `2025-11-25` de MCP y se comunica localmente mediante `stdin` y `stdout`.

## Caso de uso

El servidor está diseñado para empresas que necesitan gestionar solicitudes básicas de soporte técnico.

Permite que un cliente cree, consulte, liste y actualice tickets de soporte.

## Funcionalidades actuales (unicamente MCP)

El servidor MCP local admite los siguientes métodos:

* `initialize`
* `notifications/initialized`
* `tools/list`
* `tools/call`

Herramientas disponibles:

| Herramienta            | Propósito                        |
| ---------------------- | -------------------------------- |
| `create_ticket`        | Crea un nuevo ticket de soporte  |
| `get_ticket`           | Obtiene un ticket mediante su ID |
| `list_tickets`         | Lista los tickets existentes     |
| `update_ticket_status` | Actualiza el estado de un ticket |

La información de los tickets se almacena localmente mediante SQLite.

El proyecto también incluye un cliente MCP local que inicia el servidor como un subproceso y se comunica con él mediante JSON-RPC.

## Requisitos

* Python 3.11 o una versión posterior

## Configuración

Desde PowerShell, abre el directorio del proyecto y ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Ejecutar la demostración local de MCP

La forma más facil de probar el servidor MCP local es ejecutar:

```powershell
python -m mcp_client.demo
```

La demostración realiza automáticamente lo siguiente:

1. Inicia el servidor MCP local.
2. Realiza la inicialización de MCP.
3. Lista las herramientas disponibles.
4. Crea un ticket de soporte.
5. Obtiene el ticket creado.
6. Cierra el servidor.

Para mostrar también las interacciones JSON-RPC, ejecuta:

```powershell
python -m mcp_client.demo --mostrar-interacciones
```

Las interacciones se almacenan en:

```text
logs/mcp_interactions.log
```

Los test del MCP local son:
```text
python -m unittest tests.test_json_rpc tests.test_support_server tests.test_mcp_tools tests.test_ticket_service tests.test_mcp_client tests.test_interaction_logging
```

## Ejecutar manualmente el servidor MCP

El servidor también puede iniciarse directamente:

```powershell
python -m support_server.server
```

El servidor espera recibir un mensaje JSON-RPC por línea mediante la entrada estándar.

Para detenerlo desde PowerShell:

```text
Ctrl + Z
Enter
```

## Parámetros de las herramientas

### `create_ticket`

Parámetros:

* `usuario`: nombre del usuario
* `descripcion`: descripción del problema técnico
* `prioridad`: `low`, `medium` o `high`

Ejemplo:

```json
{
  "name": "create_ticket",
  "arguments": {
    "usuario": "Mia",
    "descripcion": "La computadora no puede conectarse a la red",
    "prioridad": "high"
  }
}
```

### `get_ticket`

Parámetros:

* `id`: ID del ticket

### `list_tickets`

No requiere parámetros.

### `update_ticket_status`

Parámetros:

* `id`: ID del ticket
* `estado`: `open`, `in_progress` o `closed`

## Pruebas

Para ejecutar todas las pruebas:

```powershell
python -m unittest discover -s tests
```

## Arquitectura del MCP local

support_server/
├── __init__.py
├── config.py
├── server.py
├── ticket_service.py
└── tools.py

database/
├── __init__.py
└── ticket_repository.py

mcp_client/
├── __init__.py
├── json_rpc.py
├── client.py
├── demo.py
└── interaction_logging.py