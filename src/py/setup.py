from __future__ import unicode_literals, print_function
import os
import shutil
import setuptools
from setuptools import setup, Command
import glob
import distutils.util
from io import open
import hashlib

KALEIDO_PY_DIR = os.path.dirname(os.path.abspath(__file__))
KALEIDO_DIR = os.path.dirname(KALEIDO_PY_DIR) # was # parent
BIN_BUILD_DIR = os.path.abspath(os.path.join(KALEIDO_PY_DIR, 'build'))
is_repo = all(
    os.path.exists(os.path.join(KALEIDO_DIR, fn)) for fn in ["version", "README.md", "LICENSE.txt"]
)

if is_repo:
    print("Running setup.py from the kaleido repository tree")
    with open(os.path.join(KALEIDO_DIR, 'version'), 'r') as f:
        version = f.read()
    with open(os.path.join(KALEIDO_DIR, "README.md"), encoding="utf8") as f:
        long_description = f.read()
else:
    print("Running setup.py during source installation")
    raise RuntimeError("Not supporting source installation through setup.py")


def list_dir_flat(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.relpath(os.path.join(path, filename), "kaleido"))
    return paths


executable_files = list_dir_flat(os.path.join("kaleido","executable")) # list of relative-to-root files to include

class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./*.pyc ./*.tgz ./*.egg-info ./kaleido/kaleido/_version.py'.split(' ')

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global KALEIDO_PY_DIR

        for path_spec in self.CLEAN_FILES:
            # Make paths absolute and relative to this path
            abs_paths = glob.glob(os.path.normpath(os.path.join(KALEIDO_PY_DIR, path_spec)))
            for path in [str(p) for p in abs_paths]:
                if not path.startswith(KALEIDO_PY_DIR):
                    # Die if path in CLEAN_FILES is absolute + outside this directory
                    raise ValueError("%s is not a path inside %s" % (path, KALEIDO_PY_DIR))
                print('removing %s' % os.path.relpath(path))
                shutil.rmtree(path)


class WriteVersion(Command):
    description = "Write _version.py file"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global KALEIDO_PY_DIR
        with open(os.path.join(KALEIDO_PY_DIR, 'kaleido', '_version.py'), 'w') as f:
                f.write('__version__ = "{version}"\n'.format(version=version))


class CopyLicenseAndReadme(Command):
    description = "Copy License and Readme files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global KALEIDO_PY_DIR
        shutil.copy(
            os.path.abspath(os.path.join(KALEIDO_PY_DIR, '..', 'LICENSE.txt')), KALEIDO_PY_DIR
        )
        shutil.copy(
            os.path.abspath(os.path.join(KALEIDO_PY_DIR, '..', 'README.md')), KALEIDO_PY_DIR 
        )


class PackageWheel(Command):
    description = "Build Wheel Package"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command("clean")
        self.run_command("write_version")
        self.run_command("copy_license")
        cmd_obj = self.distribution.get_command_obj('bdist_wheel')

        # Use current platform as plat_name, but replace linux with manylinux2014
        cmd_obj.plat_name = distutils.util.get_platform()

        # Handle windows 32-bit cross compilation
        print(os.environ.get("KALEIDO_ARCH", "x64"))
        if cmd_obj.plat_name.startswith("win-"):
            arch = os.environ.get("KALEIDO_ARCH", "x64")
            if arch == "x86":
                cmd_obj.plat_name = "win32"
            elif arch == "x64":
                cmd_obj.plat_name = "win_amd64"
            else:
                raise ValueError(
                    "Unsupported architecture {arch} for plat_name {plat_name}".format(
                        arch=arch, plat_name=cmd_obj.plat_name)
                )
        elif cmd_obj.plat_name.startswith("linux"):
            arch = os.environ.get("KALEIDO_ARCH", "x64")
            if arch == "x64":
                cmd_obj.plat_name = "manylinux1-x86_64"
            elif arch == "x86":
                cmd_obj.plat_name = "manylinux1-i686"
            elif arch == "arm64":
                cmd_obj.plat_name = "manylinux2014-aarch64"
            elif arch == "arm":
                raise RunTimeError("We're not gonna compile for regular arm, ever")

        # Set macos platform to 10.11 rather than Python environment
        elif cmd_obj.plat_name.startswith("macosx"):
            arch = os.environ.get("KALEIDO_ARCH", "x64")
            if arch == "x64":
                cmd_obj.plat_name = "macosx-10.11-x86_64"
            elif arch == "arm64":
                cmd_obj.plat_name = "macosx-11.0-arm64"

        cmd_obj.python_tag = 'py2.py3'

        package_data={
            'kaleido': executable_files,
        },
        self.run_command("bdist_wheel")

setup(
    name="kaleidofix2",
    version=version,
    author="Jon Mease",
    author_email="jon@plotly.com",
    maintainer="Andrew Pikul",
    maintainer_email="ajpikul@gmail.com",
    project_urls={"Github": "https://github.com/plotly/Kaleido"},
    description="Static image export for web-based visualization libraries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    install_requires=[
        "pathlib ; python_version<'3.4'",
    ],
    packages=["kaleido", "kaleido.scopes"],
    package_data={
        'kaleido': executable_files,
    },
    cmdclass=dict(
        clean=CleanCommand,
        write_version=WriteVersion,
        copy_license=CopyLicenseAndReadme,
        package=PackageWheel,
    )
)
