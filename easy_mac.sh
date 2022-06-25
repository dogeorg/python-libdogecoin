#!/bin/bash
(
cd ~/Downloads/libdogecoin ;
rm -rf dist ;
rm -rf build ;
rm -rf wheelhouse ;
rm wrappers/python/libdogecoin/libdogecoin.c ;
rm wrappers/python/libdogecoin/libdogecoin.o ;
# rm  ;
echo done with removing files... ;
cd ~/Downloads/python-libdc-module ;
python3 setup.py --version $1 --path $2 sdist bdist_wheel &&
mv dist/libdogecoin-$1-cp39-cp39-macosx_12_0_x86_64.whl wheels/
)
