"""Cliente MCP local implementado con subprocess y JSON-RPC manual."""

import logging
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

from mcp_client.json_rpc import (
    ErrorValidacionJsonRpc,
    construir_solicitud,
    deserializar_mensaje,
    serializar_mensaje,
)
from mcp_client.interaction_logging import RegistroInteraccionesMcp


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_PATH = PROJECT_ROOT / "logs" / "mcp_interactions.log"
SERVER_NAME = "helpdesk-mcp-server"


class ErrorClienteMcp(RuntimeError):
    """Error de comunicación o respuesta del servidor MCP."""


class TimeoutClienteMcp(ErrorClienteMcp):
    """El servidor no respondió dentro del tiempo configurado."""


class ClienteMcpLocal:
    """Administra un servidor MCP local y sus mensajes JSON-RPC."""

    def __init__(
        self,
        timeout: float = 5.0,
        environment=None,
        log_path=DEFAULT_LOG_PATH,
        mostrar_interacciones: bool = False,
    ) -> None:
        self.timeout = timeout
        self.environment = environment or {}
        self.log_path = log_path
        self.mostrar_interacciones = mostrar_interacciones
        self.proceso = None
        self.registro = None
        self._siguiente_id = 1
        self._respuestas = queue.Queue()
        self._hilos = []

    def iniciar(self) -> None:
        if self.proceso is not None and self.proceso.poll() is None:
            return

        self._siguiente_id = 1
        self._respuestas = queue.Queue()

        entorno = os.environ.copy()
        entorno.update(self.environment)
        entorno["PYTHONUTF8"] = "1"

        self.proceso = subprocess.Popen(
            [sys.executable, "-m", "support_server.server"],
            cwd=PROJECT_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=entorno,
        )
        self.registro = RegistroInteraccionesMcp(
            self.log_path, mostrar=self.mostrar_interacciones
        )

        hilo_stdout = threading.Thread(
            target=self._leer_stdout, args=(self.proceso,), daemon=True
        )
        hilo_stderr = threading.Thread(
            target=self._leer_stderr, args=(self.proceso,), daemon=True
        )
        self._hilos = [hilo_stdout, hilo_stderr]
        for hilo in self._hilos:
            hilo.start()

    def conectar(self) -> dict:
        """Inicia el servidor y completa el ciclo de inicialización MCP."""
        self.iniciar()
        resultado = self._solicitar(
            "initialize",
            {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "helpdesk-mcp-client", "version": "0.1.0"},
            },
        )
        self._notificar("notifications/initialized")
        return resultado

    def listar_herramientas(self) -> list[dict]:
        resultado = self._solicitar("tools/list", {})
        herramientas = resultado.get("tools")
        if not isinstance(herramientas, list):
            raise ErrorClienteMcp("tools/list devolvió una respuesta inválida.")
        return herramientas

    def ejecutar_herramienta(self, nombre: str, argumentos=None) -> dict:
        params = {"name": nombre, "arguments": argumentos or {}}
        return self._solicitar("tools/call", params)

    def cerrar(self) -> None:
        """Cierra stdin y espera la terminación del servidor."""
        if self.proceso is None:
            return

        proceso = self.proceso

        if proceso.stdin and not proceso.stdin.closed:
            proceso.stdin.close()

        try:
            proceso.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proceso.terminate()
            try:
                proceso.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proceso.kill()
                proceso.wait()

        for hilo in self._hilos:
            hilo.join(timeout=1)
        for flujo in (proceso.stdout, proceso.stderr):
            if flujo and not flujo.closed:
                flujo.close()

        self._hilos = []
        self.proceso = None
        if self.registro is not None:
            self.registro.cerrar()
            self.registro = None

    def _solicitar(self, method: str, params: dict) -> dict:
        id_solicitud = self._siguiente_id
        self._siguiente_id += 1
        mensaje = construir_solicitud(method, id=id_solicitud, params=params)
        self._enviar(mensaje)
        respuesta = self._recibir(method, id_solicitud)

        if respuesta.get("id") != id_solicitud:
            raise ErrorClienteMcp("La respuesta no corresponde a la solicitud enviada.")

        if "error" in respuesta:
            error = respuesta["error"]
            self._registrar_error(
                "SERVER -> CLIENT",
                method,
                id_solicitud,
                f"{error['code']}: {error['message']}",
            )
            raise ErrorClienteMcp(
                f"Error del servidor {error['code']}: {error['message']}"
            )

        return respuesta["result"]

    def _notificar(self, method: str, params=None) -> None:
        self._enviar(construir_solicitud(method, params=params))

    def _enviar(self, mensaje: dict) -> None:
        if self.proceso is None or self.proceso.poll() is not None:
            raise ErrorClienteMcp("El servidor MCP no está en ejecución.")
        if self.proceso.stdin is None:
            raise ErrorClienteMcp("No está disponible stdin del servidor.")

        try:
            texto = serializar_mensaje(mensaje)
            self._registrar_mensaje("CLIENT -> SERVER", mensaje["method"], mensaje)
            self.proceso.stdin.write(texto + "\n")
            self.proceso.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            self._registrar_error(
                "CLIENT -> SERVER", mensaje["method"], mensaje.get("id"), str(error)
            )
            raise ErrorClienteMcp("No fue posible enviar el mensaje al servidor.") from error

    def _recibir(self, method: str, id_solicitud) -> dict:
        try:
            elemento = self._respuestas.get(timeout=self.timeout)
        except queue.Empty as error:
            self._registrar_error(
                "SERVER -> CLIENT", method, id_solicitud, "Timeout de respuesta"
            )
            raise TimeoutClienteMcp("El servidor MCP no respondió a tiempo.") from error

        if isinstance(elemento, Exception):
            self._registrar_error(
                "SERVER -> CLIENT", method, id_solicitud, str(elemento)
            )
            raise ErrorClienteMcp("No fue posible leer la respuesta del servidor.") from elemento
        if elemento is None:
            self._registrar_error(
                "SERVER -> CLIENT", method, id_solicitud, "El servidor terminó"
            )
            raise ErrorClienteMcp("El servidor MCP terminó sin enviar una respuesta.")

        try:
            respuesta = deserializar_mensaje(elemento)
            self._registrar_mensaje("SERVER -> CLIENT", method, respuesta)
            return respuesta
        except ErrorValidacionJsonRpc as error:
            self._registrar_error(
                "SERVER -> CLIENT", method, id_solicitud, "Respuesta JSON-RPC inválida"
            )
            raise ErrorClienteMcp("El servidor envió una respuesta inválida.") from error

    def _registrar_mensaje(self, direccion: str, method: str, mensaje: dict) -> None:
        if self.registro is not None:
            self.registro.registrar(SERVER_NAME, direccion, method, mensaje)

    def _registrar_error(
        self, direccion: str, method: str, id_mensaje, descripcion: str
    ) -> None:
        if self.registro is not None:
            self.registro.registrar_error(
                SERVER_NAME, direccion, method, id_mensaje, descripcion
            )

    def _leer_stdout(self, proceso) -> None:
        try:
            if proceso.stdout is None:
                return
            for linea in proceso.stdout:
                if linea.strip():
                    self._respuestas.put(linea)
        except Exception as error:
            self._respuestas.put(error)
        finally:
            self._respuestas.put(None)

    def _leer_stderr(self, proceso) -> None:
        if proceso.stderr is None:
            return
        for linea in proceso.stderr:
            if linea.strip():
                logger.info("Servidor MCP: %s", linea.rstrip())

    def __enter__(self):
        try:
            self.conectar()
            return self
        except Exception:
            self.cerrar()
            raise

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.cerrar()
