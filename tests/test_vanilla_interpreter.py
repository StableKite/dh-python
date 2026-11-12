from pathlib import Path
import os
import subprocess
import sys
import sysconfig
import tempfile
from types import SimpleNamespace
from unittest import TestCase, mock

from dhpython.build.plugin_distutils import create_pydistutils_cfg
from dhpython.build.plugin_pyproject import BuildSystem


class VanillaInterpreter(TestCase):
    def test_distutils_config_is_accepted_by_selected_interpreter(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / 'home'
            home.mkdir()
            args = SimpleNamespace(home_dir=str(home), build_dir=str(root / 'build'),
                                   install_dir='/usr/lib/python3/dist-packages',
                                   interpreter=SimpleNamespace(binary_dv=sys.executable))
            context = SimpleNamespace(ENV={})

            @create_pydistutils_cfg
            def configure(self, context, args):
                return None

            configure(None, context, args)
            (root / 'setup.py').write_text('from setuptools import setup\nsetup(name="layout-probe", version="1.0", py_modules=["probe"])\n')
            (root / 'probe.py').write_text('VALUE = 42\n')
            subprocess.run([sys.executable, 'setup.py', 'install', '--root=' + str(root / 'stage')],
                           cwd=root, env=dict(os.environ, **context.ENV), check=True,
                           stdout=subprocess.DEVNULL)
            self.assertTrue((root / 'stage/usr/lib/python3/dist-packages/probe.py').is_file())
            self.assertFalse((root / 'stage/opt').exists())

    def test_pyproject_extras_use_usr_without_debian_scheme(self):
        original = sysconfig.get_paths

        def without_debian_scheme(*args, **kwargs):
            scheme = kwargs.get('scheme', args[0] if args else None)
            if scheme == 'deb_system':
                raise KeyError(scheme)
            return original(*args, **kwargs)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / 'home'
            (home / 'scripts').mkdir(parents=True)
            (home / 'scripts/probe-cli').write_text('probe')
            (home / 'data/share/probe').mkdir(parents=True)
            (home / 'data/share/probe/data.txt').write_text('payload')
            build = root / 'build'
            build.mkdir()
            (build / 'probe.py').write_text('VALUE = 42\n')
            args = SimpleNamespace(home_dir=str(home), destdir=str(root / 'stage'),
                                   build_dir=str(build), interpreter=sys.executable,
                                   install_dir='/usr/lib/python3/dist-packages')
            system = BuildSystem.__new__(BuildSystem)
            with mock.patch('dhpython.build.plugin_pyproject.sysconfig.get_paths', side_effect=without_debian_scheme):
                system.install(None, args)
            self.assertEqual((root / 'stage/usr/bin/probe-cli').read_text(), 'probe')
            self.assertEqual((root / 'stage/usr/share/probe/data.txt').read_text(), 'payload')
            self.assertTrue((root / 'stage/usr/lib/python3/dist-packages/probe.py').is_file())
            self.assertFalse((root / 'stage/opt').exists())
