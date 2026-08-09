"""Funciones básicas para construir y procesar mensajes JSON-RPC 2.0."""

import json


class ErrorValidacionJsonRpc(ValueError):
    """Indica que un texto o mensaje no cumple con JSON-RPC 2.0."""


class ErrorJsonInvalido(ErrorValidacionJsonRpc):
    """Indica que un texto no se puede interpretar como JSON."""


def construir_solicitud(method: str, id=None, params=None) -> dict:
    """Construye una solicitud o notificación JSON-RPC."""
    mensaje = {"jsonrpc": "2.0", "method": method}

    if id is not None:
        mensaje["id"] = id
    if params is not None:
        mensaje["params"] = params

    validar_mensaje(mensaje)
    return mensaje


def construir_respuesta(id, result) -> dict:
    """Construye una respuesta JSON-RPC exitosa."""
    mensaje = {"jsonrpc": "2.0", "id": id, "result": result}
    validar_mensaje(mensaje)
    return mensaje


def construir_error(id, code: int, message: str, data=None) -> dict:
    """Construye una respuesta de error JSON-RPC."""
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data

    mensaje = {"jsonrpc": "2.0", "id": id, "error": error}
    validar_mensaje(mensaje)
    return mensaje


def serializar_mensaje(mensaje: dict) -> str:
    """Valida y convierte un mensaje JSON-RPC en texto JSON."""
    validar_mensaje(mensaje)
    return json.dumps(mensaje, ensure_ascii=False)


def deserializar_mensaje(texto: str) -> dict:
    """Convierte texto JSON en un mensaje JSON-RPC validado."""
    try:
        mensaje = json.loads(texto)
    except (json.JSONDecodeError, TypeError) as error:
        raise ErrorJsonInvalido("El texto no contiene JSON válido.") from error

    validar_mensaje(mensaje)
    return mensaje


def validar_mensaje(mensaje: dict) -> None:
    """Realiza las validaciones esenciales de un mensaje JSON-RPC."""
    if not isinstance(mensaje, dict):
        raise ErrorValidacionJsonRpc("El mensaje debe ser un objeto JSON.")

    if mensaje.get("jsonrpc") != "2.0":
        raise ErrorValidacionJsonRpc("El campo 'jsonrpc' debe ser '2.0'.")

    if "method" in mensaje:
        _validar_solicitud(mensaje)
        return

    if "result" in mensaje or "error" in mensaje:
        _validar_respuesta(mensaje)
        return

    raise ErrorValidacionJsonRpc("El mensaje está incompleto.")


def _validar_solicitud(mensaje: dict) -> None:
    method = mensaje.get("method")
    if not isinstance(method, str) or not method:
        raise ErrorValidacionJsonRpc("El campo 'method' debe ser texto no vacío.")

    if "id" in mensaje:
        _validar_id(mensaje["id"], permitir_nulo=False)

    if "params" in mensaje and not isinstance(mensaje["params"], (dict, list)):
        raise ErrorValidacionJsonRpc("El campo 'params' debe ser un objeto o arreglo.")

    if "result" in mensaje or "error" in mensaje:
        raise ErrorValidacionJsonRpc("Una solicitud no puede contener 'result' o 'error'.")


def _validar_respuesta(mensaje: dict) -> None:
    if "id" not in mensaje:
        raise ErrorValidacionJsonRpc("Una respuesta debe contener el campo 'id'.")

    _validar_id(mensaje["id"], permitir_nulo=True)

    tiene_resultado = "result" in mensaje
    tiene_error = "error" in mensaje
    if tiene_resultado == tiene_error:
        raise ErrorValidacionJsonRpc(
            "Una respuesta debe contener solamente 'result' o 'error'."
        )

    if tiene_error:
        error = mensaje["error"]
        if not isinstance(error, dict):
            raise ErrorValidacionJsonRpc("El campo 'error' debe ser un objeto.")
        if not isinstance(error.get("code"), int) or isinstance(error.get("code"), bool):
            raise ErrorValidacionJsonRpc("El código de error debe ser un entero.")
        if not isinstance(error.get("message"), str):
            raise ErrorValidacionJsonRpc("El mensaje de error debe ser texto.")


def _validar_id(id, permitir_nulo: bool) -> None:
    tipos_validos = (str, int)
    if isinstance(id, bool) or not isinstance(id, tipos_validos):
        if permitir_nulo and id is None:
            return
        raise ErrorValidacionJsonRpc("El campo 'id' debe ser texto o un entero.")
