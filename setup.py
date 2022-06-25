import sys
from setuptools import setup, Extension, Command
from Cython.Build import cythonize
from Cython.Distutils import build_ext

# set defaults
depends_lib = "x86_64-pc-linux-gnu"
version = "0.0.1"

# assess command line flags
i=0
while i < len(sys.argv):
    flag = sys.argv[i]
    if flag == "--depends_lib":
        arg = sys.argv[i+1]
        assert arg in ("arm-linux-gnueabihf",
                            "aarch64-linux-gnu",
                            "x86_64-pc-linux-gnu",
                            "x86_64-apple-darwin14",
                            "x86_64-w64-mingw32",
                            "i686-w64-mingw32",
                            "i686-pc-linux-gnu",), "Invalid architecture."
        depends_lib = arg
        del sys.argv[i+1]
        del sys.argv[i]
        continue
    if flag == "--version":
        arg = sys.argv[i+1]
        assert input(f"version {arg} ok? (y/n) ")=='y', "Aborting setup."
        version = arg
        del sys.argv[i+1]
        del sys.argv[i]
        continue
    i += 1
print(sys.argv)

        
libdoge_extension = [Extension(
    name=               "libdogecoin",
    language=           "c",
    sources=            ["/home/jmcaninch/libdogecoin/wrappers/python/libdogecoin/libdogecoin.pyx"],
    include_dirs=       ["/home/jmcaninch/libdogecoin",
                        "/home/jmcaninch/libdogecoin/include",
                        "/home/jmcaninch/libdogecoin/include/dogecoin",
                        "/home/jmcaninch/libdogecoin/secp256k1/include"],
    libraries =         ["event", "event_core", "pthread", "m"],
    library_dirs =      ["depends/" + depends_lib + "/lib"],
    extra_objects=      ["/home/jmcaninch/libdogecoin/.libs/libdogecoin.a"],
    extra_compile_args= ["--static", "-fPIC"]
)]

setup(
    name=                           "libdogecoin",
    version=                        version, 
    author=                         "Jackie McAninch",
    author_email=                   "jackie.mcaninch.2019@gmail.com",
    description=                    "Python interface for the libdogecoin C library",
    long_description=               open("PYPI_README.md", "r").read(),
    long_description_content_type=  "text/markdown",
    license=                        "MIT",
    url=                            "https://github.com/dogecoinfoundation/libdogecoin",
    classifiers=                    ["Programming Language :: Python :: 3",
                                     "License :: OSI Approved :: MIT License",
                                     "Operating System :: POSIX :: Linux"],
    cmdclass =                      {'build_ext': build_ext},
    ext_modules=                    cythonize(libdoge_extension, language_level = "3")
)
