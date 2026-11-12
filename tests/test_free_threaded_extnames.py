import unittest
import sys
import sysconfig
import tempfile
from pathlib import Path
from unittest.mock import patch

from dhpython.interpreter import Interpreter


class TestFreeThreadedExtensionNames(unittest.TestCase):
    def check_name(self, version: str, soabi: str, filename: str) -> str | None:
        interpreter = Interpreter("python" + version)
        with patch.object(
            interpreter, "_get_config", return_value=[soabi, "MYARCH", "", "", ""]
        ):
            return interpreter.check_extname(filename)

    def test_abi3t_filename(self) -> None:
        self.assertEqual(
            self.check_name("3.15", "cpython-315t", "foo.abi3t.so"),
            "foo.abi3t-MYARCH.so",
        )

    def test_abi3t_filename_on_gil_build(self) -> None:
        # PEP 803 makes abi3t filenames loadable by both builds from 3.15.
        self.assertEqual(
            self.check_name("3.15", "cpython-315", "foo.abi3t.so"),
            "foo.abi3t-MYARCH.so",
        )

    def test_abi3t_requires_python315(self) -> None:
        for version, soabi in (("3.13", "cpython-313t"), ("3.14", "cpython-314t")):
            with self.subTest(version=version):
                self.assertIsNone(self.check_name(version, soabi, "foo.abi3t.so"))

    def test_gil_stable_abi_is_not_free_threaded(self) -> None:
        for soabi in ("cpython-315t", "cpython-315td"):
            with self.subTest(soabi=soabi):
                self.assertIsNone(self.check_name("3.15", soabi, "foo.abi3.so"))

    def test_gil_stable_abi_is_preserved(self) -> None:
        self.assertEqual(
            self.check_name("3.15", "cpython-315", "foo.abi3.so"),
            "foo.abi3-MYARCH.so",
        )

    def test_already_tagged_stable_abi_is_not_renamed(self) -> None:
        self.assertIsNone(
            self.check_name("3.15", "cpython-315t", "foo.abi3t-MYARCH.so")
        )

    def test_version_specific_abi_is_preserved(self) -> None:
        self.assertEqual(
            self.check_name("3.15", "cpython-315t", "foo.so"),
            "foo.cpython-315t-MYARCH.so",
        )
        self.assertIsNone(self.check_name("3.15", "cpython-315t", "foo.cpython-315.so"))

    def test_real_interpreter_configuration(self) -> None:
        version = ".".join(map(str, sys.version_info[:2]))
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / ("python" + version)).symlink_to(sys.executable)
            interpreter = Interpreter("python" + version, path=folder + "/")
            soabi, multiarch = interpreter._get_config()[:2]
            expected = sysconfig.get_config_var("SOABI").replace(
                "-" + sysconfig.get_config_var("MULTIARCH"), ""
            )
            self.assertEqual(soabi, expected)
            self.assertEqual(
                interpreter.check_extname("foo.so"), f"foo.{soabi}-{multiarch}.so"
            )
