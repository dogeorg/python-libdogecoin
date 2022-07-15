#!/bin/bash
echo "usage: ./easy_windows.sh <version_no> <abs_path_to_libdogecoin> <abs_path_to_current>"
(
cd $2 ;
rm -rf dist 2> /dev/null;
rm -rf build 2> /dev/null;
rm -rf wheelhouse 2> /dev/null;
rm wrappers/python/libdogecoin/libdogecoin.c 2> /dev/null;
rm wrappers/python/libdogecoin/libdogecoin.o 2> /dev/null;
echo "done removing files..." ;
cd $3 ;
python3 setup.py --version $1 --path $2 sdist bdist_wheel #&&
# mv dist/[name on windows].whl wheels/
)
