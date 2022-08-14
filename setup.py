import os
import subprocess
import sys
from setuptools import setup, Extension, Command
from Cython.Build import cythonize
from Cython.Distutils import build_ext

class config(Command):
    """
    A command class to runs the client GUI.
    """

    description = "Configuration options for build."

    # The format is (long option, short option, description).
    user_options = [
        ('host=', None, 'The target host triplet'),
        ('version=', None, 'The version to build'),
    ]

    def initialize_options(self):
        """
        Sets the default value for the server socket.

        The method is responsible for setting default values for
        all the options that the command supports.

        Option dependencies should not be set here.
        """
        global version
        self.version = '0.1.0'
        version = self.version
        self.host = os.environ.get('host')

    def finalize_options(self):
        """
        Overriding a required abstract method.

        The method is responsible for setting and checking the 
        final values and option dependencies for all the options 
        just before the method run is executed.

        In practice, this is where the values are assigned and verified.
        """
        assert self.host in ("arm-linux-gnueabihf",
                            "aarch64-linux-gnu",
                            "x86_64-pc-linux-gnu",
                            "x86_64-apple-darwin14",
                            "x86_64-w64-mingw32",
                            "i686-w64-mingw32",
                            "i686-pc-linux-gnu",), "Invalid architecture."

        pass

    def run(self):
        """
        Semantically, runs 'python fetch.py' on the
        command line.
        """
        print('self.host')
        print(self.host)
        if self.host == ("i686-w64-mingw32" or "x86_64-w64-mingw32"):
            if self.host == "i686-w64-mingw32":
                arch = "win32"
            else:
                arch = "amd64"
            errno = subprocess.call(['./bin/init --arch=' + arch], shell=True)
            print(errno)
            if errno != 0:
                raise SystemExit("Unable to build for windows!")
        else:
            errno = subprocess.call(['./dist.sh  --host=' + self.host], shell=True)
            print(errno)
            if errno != 0:
                raise SystemExit("Unable to build for unix based systems!")

# set defaults
version = "0.1.0"
    
libdogecoin_extension = [Extension(
    name=               "libdogecoin",
    language=           "c",
    sources=            ["libdogecoin.pyx"],
    include_dirs=       ["include"],
    library_dirs =      ["lib"],
    extra_objects=      ["lib/" + os.environ.get('host') + "/libdogecoin.a"],
)]

setup(
    name=                           "libdogecoin",
    version=                        version,
    author=                         "Jackie McAninch",
    author_email=                   "jackie.mcaninch.2019@gmail.com",
    maintainer=                     "bluezr",
    maintainer_email=               "bluezr@dogecoin.com",
    description=                    "Python interface for the libdogecoin C library",
    long_description=               open("README.md", "r").read(),
    long_description_content_type=  "text/markdown",
    license=                        "AGPL-3.0",
    url=                            "https://github.com/dogecoinfoundation/libdogecoin",
    classifiers=                    ["Programming Language :: Python :: 3",
                                     "License :: OSI Approved :: MIT License",
                                     "Operating System :: POSIX :: Linux"],
    cmdclass=                       {'build_ext': build_ext, 'config': config},
    ext_modules=                    cythonize(libdogecoin_extension, language_level = "3"),
    include_package_data=           True,
    packages=                       ['tests'],
)
