"""python-libdogecoin - cffi build.

Swapped from Cython to cffi. The native extension is built out-of-line via
cffi_modules, pointing at python/_build.py:ffibuilder. fetch.py still populates
./lib/libdogecoin.a and ./include/libdogecoin.h exactly as before; the cdef is
generated from that fetched header by codegen/gen_cdef.py at build time, so the
bound surface tracks the fetched libdogecoin release.
"""
from setuptools import setup

setup(
    name="libdogecoin",
    version="0.1.4",
    maintainer="bluezr",
    maintainer_email="bluezr@dogecoin.com",
    description="Python interface for the libdogecoin C library",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/dogeorg/python-libdogecoin",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
    ],
    package_dir={"": "python"},
    packages=["libdogecoin"],
    package_data={"libdogecoin": ["_cdef.h", "_surface.json", "py.typed", "__init__.pyi"]},
    python_requires=">=3.10",
    setup_requires=["cffi>=1.16"],
    cffi_modules=["python/_build.py:ffibuilder"],
    install_requires=["cffi>=1.16"],
    include_package_data=True,
    # One stable-ABI wheel per platform covers CPython 3.10 through 3.13+.
    options={"bdist_wheel": {"py_limited_api": "cp310"}},
)
