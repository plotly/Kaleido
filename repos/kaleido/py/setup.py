import setuptools
import os
import shutil
from setuptools import setup, Command

here = os.path.dirname(os.path.abspath(__file__))

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


class CopyExecutable(Command):
    description = "Copy Kaleido executable directory into package"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        shutil.rmtree(os.path.join(here, 'kaleido', 'executable'), ignore_errors=True)
        shutil.copytree(
            os.path.join(here, '..', '..', 'build', 'kaleido'),
            os.path.join(here, 'kaleido', 'executable')
        )

setup(
    name="kaleido",
    version="0.0.1a2",
    packages=["kaleido", "kaleido.scopes"],
    package_data={'kaleido': package_files("kaleido/executable")},
    cmdclass=dict(
        copy_executable=CopyExecutable,
    )
)
