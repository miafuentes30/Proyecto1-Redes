# Proyecto 1 - Redes

Chatbot de consola que funcionará como anfitrión de servidores MCP. El proyecto
implementará manualmente el protocolo MCP mediante mensajes JSON-RPC 2.0, sin
utilizar SDK o frameworks de MCP.

## Estado actual

El proyecto contiene una capa manual JSON-RPC 2.0 y un servidor MCP local
compatible con la versión `2025-11-25`. El servidor admite `initialize`,
`notifications/initialized`, `tools/list` y `tools/call` mediante `stdin` y
`stdout`.

Las herramientas `create_ticket`, `get_ticket`, `list_tickets` y
`update_ticket_status` utilizan persistencia local SQLite. El chatbot de consola
usa la API de Anthropic para preguntas generales y para decidir cuándo ejecutar
estas herramientas mediante nuestro cliente MCP.

El cliente MCP local inicia el servidor como subproceso, completa la
inicialización y permite listar o ejecutar herramientas mediante JSON-RPC.

## Requisitos

- Python 3.11 o posterior.

## Preparación

Desde PowerShell, en la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Ejecución

Configure la API key en la sesión actual de PowerShell:

```powershell
$env:ANTHROPIC_API_KEY = "su-api-key"
```

Opcionalmente, puede seleccionar otro modelo:

```powershell
$env:ANTHROPIC_MODEL = "claude-sonnet-5"
```

Inicie el chatbot:

```powershell
python main.py
```

El historial se conserva solamente en memoria mientras el programa está
abierto. Escriba `limpiar` para borrar el contexto actual o `salir` para cerrar
la sesión.

Para iniciar el servidor MCP local:

```powershell
python -m support_server.server
```

El servidor espera un mensaje JSON-RPC completo por línea. Para finalizarlo,
presione `Ctrl+Z` y luego `Enter` en PowerShell.

Para ejecutar la demostración completa del cliente local:

```powershell
python -m mcp_client.demo
```

Las interacciones se guardan en `logs/mcp_interactions.log`. Para mostrarlas
también durante la demostración:

```powershell
python -m mcp_client.demo --mostrar-interacciones
```

## Pruebas

```powershell
python -m unittest discover -s tests
```
