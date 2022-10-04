from setuptools import setup, Extension, Command
from setuptools.command.install import install
from distutils.command import build as build_module
from Cython.Build import cythonize
from Cython.Distutils import build_ext
import os
import argparse
import subprocess

depends_lib = ""

class BuildDepends(Command):
    user_options = [
        ('host=', None, "Specify the host architecture.")
    ]
    def initialize_options(self):
        self.host = "x86_64-pc-linux-gnu"
    def finalize_options(self):
        assert self.host in ("arm-linux-gnueabihf",
                            "aarch64-linux-gnu",
                            "x86_64-pc-linux-gnu",
                            "x86_64-apple-darwin11",
                            "x86_64-w64-mingw32",
                            "i686-w64-mingw32",
                            "i686-pc-linux-gnu",), "Invalid architecture."
    def run(self):
        global depends_lib
        depends_lib = self.host
       
# set defaults
version = "0.1.0"
       
libdogecoin_extension = [Extension(
    name=               "libdogecoin",
    language=           "c",
    sources=            ["libdogecoin.pyx"],
    include_dirs=       ["include"],
    library_dirs =      ["lib"],
    extra_objects=      ["lib/" + depends_lib + "/libdogecoin.a"],
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
    cmdclass =                      {'build_ext': build_ext,
                                    'build_depends': BuildDepends},
    ext_modules=                    cythonize(libdogecoin_extension, language_level = "3"),
    include_package_data=           True,
    packages=                       ['tests'],
)
