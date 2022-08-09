import os
import sys
from setuptools import setup, Extension, Command
from Cython.Build import cythonize
from Cython.Distutils import build_ext

# set defaults
version = os.environ.get("version", "0.1.0")
       
libdoge_extension = [Extension(
    name=               "libdogecoin",
    language=           "c",
    sources=            ["libdogecoin.pyx"],
    include_dirs=       ["include/"],
    library_dirs =      ["lib/"],
    extra_objects=      ["lib/libdogecoin.a"],
)]

setup(
    name=                           "libdogecoin",
    version=                        version, 
    author=                         ["Jackie McAninch", "bluezr"],
    author_email=                   ["jackie.mcaninch.2019@gmail.com", "bluezr@dogecoin.com"],
    description=                    "Python interface for the libdogecoin C library",
    long_description=               open("README.md", "r").read(),
    long_description_content_type=  "text/markdown",
    license=                        "AGPL-3.0",
    url=                            "https://github.com/dogecoinfoundation/libdogecoin",
    classifiers=                    ["Programming Language :: Python :: 3",
                                     "License :: OSI Approved :: MIT License",
                                     "Operating System :: POSIX :: Linux"],
    cmdclass=                      {'build_ext': build_ext},
    ext_modules=                    cythonize(libdoge_extension, language_level = "3")
)
