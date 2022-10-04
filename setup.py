from setuptools import setup, Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

# set defaults
version = "0.1.0"
       
libdogecoin_extension = [Extension(
    name=               "libdogecoin",
    language=           "c",
    sources=            ["libdogecoin.pyx"],
    include_dirs=       ["include"],
    library_dirs =      ["lib"],
    extra_objects=      ["lib/libdogecoin.a"],
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
    cmdclass =                      {'build_ext': build_ext},
    ext_modules=                    cythonize(libdogecoin_extension, language_level = "3"),
    include_package_data=           True,
    packages=                       ['tests'],
)
