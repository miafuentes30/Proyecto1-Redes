"""Pruebas del punto de entrada básico."""

import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from chatbot.app import ejecutar


class AppTest(unittest.TestCase):
    def test_ejecutar_informa_si_falta_api_key(self) -> None:
        salida = io.StringIO()

        with patch.dict(os.environ, {}, clear=True):
            with redirect_stdout(salida):
                ejecutar()

        self.assertIn("ANTHROPIC_API_KEY", salida.getvalue())


if __name__ == "__main__":
    unittest.main()
