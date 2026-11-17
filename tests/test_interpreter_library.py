import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dhpython.interpreter import Interpreter


class TestInterpreterLibrary(unittest.TestCase):
    def test_shared_library_outside_config_directory(self):
        with tempfile.TemporaryDirectory() as work:
            libdir = Path(work)
            libpl = libdir / "config"
            libpl.mkdir()
            library = "libpython3.15t.so"
            (libpl / library.replace(".so", ".a")).touch()
            shared = libdir / library
            shared.touch()
            interpreter = Interpreter("python3.15")
            config = ["cpython-315t", "MYARCH", "", str(libpl), library, str(libdir)]
            with patch.object(interpreter, "_get_config", return_value=config):
                self.assertEqual(interpreter.library_file, str(shared))

    def test_existing_config_library_is_preserved(self):
        with tempfile.TemporaryDirectory() as work:
            libdir = Path(work)
            libpl = libdir / "config"
            libpl.mkdir()
            library = "libpython3.15.so"
            (libdir / library).touch()
            (libpl / library).touch()
            interpreter = Interpreter("python3.15")
            config = ["cpython-315", "MYARCH", "", str(libpl), library, str(libdir)]
            with patch.object(interpreter, "_get_config", return_value=config):
                self.assertEqual(interpreter.library_file, str(libpl / library))
