import setuptools
import os
import shutil
from setuptools import setup, Command
import glob
import distutils.util

here = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(os.path.dirname(here), 'version'), 'r') as f:
    version = f.read()

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


executable_files = package_files("kaleido/executable")

class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./dist ./*.pyc ./*.tgz ./*.egg-info'.split(' ')

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global here

        for path_spec in self.CLEAN_FILES:
            # Make paths absolute and relative to this path
            abs_paths = glob.glob(os.path.normpath(os.path.join(here, path_spec)))
            for path in [str(p) for p in abs_paths]:
                if not path.startswith(here):
                    # Die if path in CLEAN_FILES is absolute + outside this directory
                    raise ValueError("%s is not a path inside %s" % (path, here))
                print('removing %s' % os.path.relpath(path))
                shutil.rmtree(path)


class CopyExecutable(Command):
    description = "Copy Kaleido executable directory into package"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        output_dir = os.path.join(here, 'kaleido', 'executable')
        input_dir = os.path.abspath(os.path.join(here, '..', '..', 'build', 'kaleido'))

        print("copy_executable: Deleting {output_dir}".format(output_dir=output_dir))
        shutil.rmtree(output_dir, ignore_errors=True)

        print("copy_executable: Copying {input_dir} to {output_dir}".format(
            input_dir=input_dir, output_dir=output_dir)
        )
        shutil.copytree(
            input_dir,
            output_dir
        )

        # Recompute executable files
        del executable_files[:]
        executable_files.extend(package_files("kaleido/executable"))


class WriteVersion(Command):
    description = "Write _version.py file"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        with open(os.path.join(here, 'kaleido', '_version.py'), 'w') as f:
            f.write('__version__ = "{version}"\n'.format(version=version))


class CopyLicense(Command):
    description = "Copy License files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        shutil.copy(
            os.path.abspath(os.path.join(here, '..', 'LICENSE.txt')), here
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
        self.run_command("copy_executable")
        self.run_command("write_version")
        self.run_command("copy_license")
        cmd_obj = self.distribution.get_command_obj('bdist_wheel')

        # Use current platform as plat_name, but replace linux with manylinux2014
        cmd_obj.plat_name = distutils.util.get_platform().replace("linux-", "manylinux2014-")
        cmd_obj.python_tag = 'py2.py3'
        self.run_command("bdist_wheel")


def readme():
    with open(os.path.join(here, "..", "README.md")) as f:
        return f.read()


setup(
    name="kaleido",
    version=version,
    author="Jon Mease",
    author_email="jon@plotly.com",
    maintainer="Jon Mease",
    maintainer_email="jon@plotly.com",
    project_urls={"Github": "https://github.com/plotly/Kaleido"},
    description="Static image export for web-based visualization libraries with zero dependencies",
    long_description=readme(),
    long_description_content_type="text/markdown",
    license="MIT",
    packages=["kaleido", "kaleido.scopes"],
    package_data={
        'kaleido': executable_files,
    },
    cmdclass=dict(
        copy_executable=CopyExecutable,
        clean=CleanCommand,
        write_version=WriteVersion,
        copy_license=CopyLicense,
        package=PackageWheel,
    )
)
