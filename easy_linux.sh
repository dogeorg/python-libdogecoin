#!/bin/bash
(
cd /home/jmcaninch/libdogecoin ;
rm -rf dist ;
rm -rf build ;
rm -rf wheelhouse ;
rm wrappers/python/libdogecoin/libdogecoin.c ;
rm wrappers/python/libdogecoin/libdogecoin.o ;
rm libdogecoin-$1-cp38-cp38-linux_x86_64.whl ;
echo done with removing files... ;
cd /home/jmcaninch/py-libdc-module ;
python3 setup.py --version 0.0.3 sdist bdist_wheel &&
auditwheel repair --plat manylinux2014_x86_64 dist/libdogecoin-$1-cp38-cp38-linux_x86_64.whl -w ./wheels &&
cd /home/jmcaninch/py-libdc-module
)
