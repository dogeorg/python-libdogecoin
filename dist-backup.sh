#!/bin/bash
export LC_ALL=C
set -e -o pipefail

if [ $# -eq 0 ]; then
    echo "No arguments provided"
    exit 1
fi

config_env() {
    case "$TARGET_HOST_TRIPLET" in
        "arm-linux-gnueabihf")
            OS=linux
            TARGET_ARCH="armv7l"
        ;;
        "aarch64-linux-gnu")
            OS=linux
            TARGET_ARCH="aarch64"
        ;;
        "x86_64-w64-mingw32")
            OS=linux
            TARGET_ARCH="amd64"
            IMAGE=ubuntu:22.04
        ;;
        "i686-w64-mingw32")
            OS=linux
            TARGET_ARCH="amd64"
            IMAGE=ubuntu:22.04
        ;;
        "x86_64-apple-darwin14")
            OS=darwin
            TARGET_ARCH="amd64"
        ;;
        "x86_64-pc-linux-gnu")
            OS=linux
            TARGET_ARCH="x86_64"
        ;;
        "i686-pc-linux-gnu")
            OS=linux
            TARGET_ARCH="i386"
        ;;
        "all")
            ALL_HOST_TRIPLETS=("x86_64-pc-linux-gnu" "i686-pc-linux-gnu" "aarch64-linux-gnu" "arm-linux-gnueabihf" "x86_64-apple-darwin14")
        ;;
        *)
            ERROR=1
        ;;
    esac
}

ALL_HOST_TRIPLETS=""
TARGET_HOST_TRIPLET=""
for i in "$@"
do
case $i in
    -h=*|--host=*)
        HOST="${i#*=}"
        TARGET_HOST_TRIPLET=($HOST)
        config_env
    ;;
    *)
        ERROR=1
    ;;
esac
done

if [ "$ERROR" ]; then
    echo "Please provide a host to build and try again."
    exit $ERROR
fi

build() {
    if [ "$TARGET_HOST_TRIPLET" == "x86_64-w64-mingw32" ] || [ "$TARGET_HOST_TRIPLET" == "i686-w64-mingw32" ]; then
        if [ "$TARGET_HOST_TRIPLET" == "x86_64-w64-mingw32" ]; then
            arch=amd64    
            host=i686-w64-mingw32
            plat=win32
            nuget=pythonx86
        elif [ "$TARGET_HOST_TRIPLET" == "i686-w64-mingw32" ]; then
            arch=win32
            host=x86_64-w64-mingw32
            plat=win_amd64
            nuget=python
        fi
        # ./bin/init --arch=$arch
        _pth=`find . -maxdepth 3 -type f -regex ".*$arch/python.exe"`
        _pth="${_pth%/*}"
        p=$_pth/python.exe
        # install wheel dependencies:
        $p -m pip install -r requirements.txt

        # fetch and link missing libs in libdogecoin.a
        # $p fetch.py --host=$host

        # build and test python wheel
        # $p -m set --host=$host
        $p -m build -s -w
        TARGET_WHEEL=$(find . -maxdepth 2 -type f -regex "./dist/.*libdogecoin-.*$plat.whl")
        $p -m pip install --upgrade wheel pytest
        $p -m wheel unpack "$TARGET_WHEEL"
        tarfile="${TARGET_WHEEL%/*}/libdogecoin-0.1.0.tar.gz"
        tar xvf $tarfile
        # cp -r ./tests ./libdogecoin-0.1.0/
        pushd ./libdogecoin-0.1.0
            .$p -m pytest
        popd
        cp $TARGET_WHEEL $tarfile ./wheels
        # p=python
        # # $p -m set --host=$host
        # $p -m build -C--plat-name=$arch -s -w
        # TARGET_WHEEL=$(find . -maxdepth 2 -type f -regex "./dist/.*libdogecoin-.*.whl")
        # $p -m pip install --upgrade wheel pytest
        # $p -m wheel unpack "$TARGET_WHEEL"
        # tarfile="${TARGET_WHEEL%/*}/libdogecoin-0.1.0.tar.gz"
        # tar xvf $tarfile
        # # cp -r ./tests ./libdogecoin-0.1.0/
        # pushd ./libdogecoin-0.1.0
        #     $p -m pytest
        # popd
        # cp $TARGET_WHEEL $tarfile ./wheels
    else
        # build and test python wheel
        p=python
        $p -m set --host=$host
        $p -m build -s -w
        TARGET_WHEEL=$(find . -maxdepth 2 -type f -regex "./dist/.*libdogecoin-.*.whl")
        $p -m pip install --upgrade wheel pytest
        $p -m wheel unpack "$TARGET_WHEEL"
        tarfile="${TARGET_WHEEL%/*}/libdogecoin-0.1.0.tar.gz"
        tar xvf $tarfile
        # cp -r ./tests ./libdogecoin-0.1.0/
        pushd ./libdogecoin-0.1.0
            $p -m pytest
        popd
        cp $TARGET_WHEEL $tarfile ./wheels
    fi
    # rm -rf ./tmp ./build ./dist ./libdogecoin.egg-info libdogecoin.c .pytest_cache *.exe *.asc
}

if [[ "$ALL_HOST_TRIPLETS" != "" ]]; then
    END=$((${#ALL_HOST_TRIPLETS[@]} - 1))
    for i in "${!ALL_HOST_TRIPLETS[@]}"
    do
    :
        TARGET_HOST_TRIPLET="${ALL_HOST_TRIPLETS[$i]}"
        config_env
        build
    done
else
        config_env
        build 
fi