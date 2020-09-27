from __future__ import unicode_literals, print_function
import os
import shutil
from setuptools import setup, Command
import glob
import distutils.util
from io import open
import hashlib

here = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(here)
executable_build_dir = os.path.abspath(os.path.join(here, '..', '..', 'build'))
is_repo = all(
    os.path.exists(os.path.join(parent, fn)) for fn in ["version", "README.md", "LICENSE.txt"]
)

if is_repo:
    print("Running setup.py from the kaleido repository tree")
    with open(os.path.join(os.path.dirname(here), 'version'), 'r') as f:
        version = f.read()
    with open(os.path.join(here, "..", "README.md"), encoding="utf8") as f:
        long_description = f.read()
else:
    print("Running setup.py during source installation")
    # Follow this path on source package installation
    with open(os.path.join(here, 'kaleido', '_version.py'), 'r') as f:
        version_py = f.read()
    version = eval(version_py.strip().split("=")[1])
    long_description = None


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


executable_files = package_files("kaleido/executable")


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./*.pyc ./*.tgz ./*.egg-info ./kaleido/kaleido/_version.py ./kaleido/executable'.split(' ')

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
        input_dir = os.path.abspath(os.path.join(executable_build_dir, 'kaleido'))

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


class CopyLicenseAndReadme(Command):
    description = "Copy License and Readme files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        shutil.copy(
            os.path.abspath(os.path.join(here, '..', 'LICENSE.txt')), here
        )
        shutil.copy(
            os.path.abspath(os.path.join(here, '..', 'README.md')), here
        )


class PackageSourceDistribution(Command):
    description = "Build source distribution package"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command("clean")
        self.run_command("write_version")
        self.run_command("copy_license")

        # Remove executable files
        del executable_files[:]

        self.run_command("sdist")


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
                cmd_obj.plat_name = "manylinux2014-armv7l"

        # Set macos platform to 10.10 to match chromium build target (See build/config/mac/mac_sdk.gni)
        # rather than Python environment
        elif cmd_obj.plat_name.startswith("macosx"):
            cmd_obj.plat_name = "macosx-10.10-x86_64"

        cmd_obj.python_tag = 'py2.py3'
        self.run_command("bdist_wheel")


class HashBundleArtifacts(Command):
    description = "Zip and hash archives, gather to single zip"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import platform
        artifacts_dir = os.path.join(parent, 'artifacts')
        python_dist_dir = os.path.join(here, 'dist')
        # Create fresh empty artifacts directory
        if os.path.exists(artifacts_dir):
            shutil.rmtree(artifacts_dir)
        os.makedirs(artifacts_dir)

        # Copy python packages
        for fn in os.listdir(python_dist_dir):
            if fn.endswith(".tar.gz") or fn.endswith(".whl"):
                shutil.copyfile(
                    os.path.join(here, "dist", fn), os.path.join(artifacts_dir, fn)
                )

        # Copy executable
        system = platform.system()
        if system == "Windows":
            arch = os.environ["KALEIDO_ARCH"]
            suffix = "win_" + arch
        elif system == "Linux":
            arch = os.environ["KALEIDO_ARCH"]
            suffix = "linux_" + arch
        elif system == "Darwin":
            suffix = "mac"
        else:
            raise ValueError("Unknown system {system}".format(system=system))

        # Full executable
        input_dir = os.path.abspath(os.path.join(executable_build_dir, 'kaleido'))
        output_base = os.path.join(artifacts_dir, "kaleido_{suffix}".format(suffix=suffix))
        shutil.make_archive(output_base, "zip", input_dir)

        # Minimal executable, if any
        input_dir = os.path.abspath(os.path.join(executable_build_dir, 'kaleido_minimal'))
        if os.path.exists(input_dir):
            output_base = os.path.join(artifacts_dir, "kaleido_minimal_{suffix}".format(suffix=suffix))
            shutil.make_archive(output_base, "zip", input_dir)

        # Write hash files
        for fn in list(os.listdir(artifacts_dir)):
            in_filepath = os.path.join(artifacts_dir, fn)
            out_filepath = os.path.join(artifacts_dir, fn + ".sha256")
            with open(in_filepath, "rb") as in_f:
                file_bytes = in_f.read() # read entire file as bytes
                readable_hash = hashlib.sha256(file_bytes).hexdigest()
                with open(out_filepath, "wt") as out_f:
                    out_f.write(readable_hash)

        # Write all artifacts into single zip file
        output_base = os.path.join(
            os.path.dirname(artifacts_dir),
            "kaleido_artifacts_{suffix}".format(suffix=suffix)
        )
        output_zipfile = output_base + ".zip"
        if os.path.exists(output_zipfile):
            os.remove(output_zipfile)
        print("Writing artifacts archive to {output_zipfile} ... ".format(
            output_zipfile=output_zipfile
        ), end="")
        shutil.make_archive(output_base, "zip", artifacts_dir)
        print("done")

setup(
    name="kaleido",
    version=version,
    author="Jon Mease",
    author_email="jon@plotly.com",
    maintainer="Jon Mease",
    maintainer_email="jon@plotly.com",
    project_urls={"Github": "https://github.com/plotly/Kaleido"},
    description="Static image export for web-based visualization libraries with zero dependencies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=["kaleido", "kaleido.scopes"],
    package_data={
        'kaleido': executable_files,
    },
    cmdclass=dict(
        package_source=PackageSourceDistribution,
        copy_executable=CopyExecutable,
        clean=CleanCommand,
        write_version=WriteVersion,
        copy_license=CopyLicenseAndReadme,
        package=PackageWheel,
        bundle_hash_artifacts=HashBundleArtifacts,
    )
)
