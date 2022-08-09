#!/bin/bash
export LC_ALL=C
set -e -o pipefail

if [ $# -eq 0 ]; then
    echo "No arguments provided"
    exit 1
fi

has_param() {
    local term="$1"
    shift
    for arg; do
        if [[ $arg == "$term" ]]; then
            return 0
        fi
    done
    return 1
}

check_sig() {
    if gpg --verify $1 $2; then
        printf "$green> GPG signature looks good$reset\n"
    else
        printf "$red> GPG signature for this libdogecoin release is invalid! This is BAD and may mean the release has been tampered with. It is strongly recommended that you report this to the libdogecoin developers.$reset\n"
        exit 1;
    fi
}

check_tools() {
    for cmd in "$@"; do
        if ! command -v "$cmd" > /dev/null 2>&1; then
            echo "ERR: This script requires that '$cmd' is installed and available in your \$PATH"
            echo $@
            apt-get update
            apt-get -y install $@
        fi
    done
}

TAG=""
OS=""
ARCH=""
ML=""
ALL_HOST_TRIPLETS=""
TARGET_HOST_TRIPLET=""
for i in "$@"
do
case $i in
    -h=*|--host=*)
        HOST="${i#*=}"
        ALL_HOST_TRIPLETS=($HOST)
        case "$ALL_HOST_TRIPLETS" in
            "arm-linux-gnueabihf")
                OS=linux
                ARCH=armv7l
                ML=linux_armv7l
                ARCH_PACKAGES+="g++-arm-linux-gnueabihf "
                ARCH_PACKAGES+="qemu-user-static qemu-user"
                TARGET_ARCH="armhf"
            ;;
            "aarch64-linux-gnu")
                OS=linux
                ARCH=aarch64
                ML=manylinux2014_aarch64
                ARCH_PACKAGES+="g++-aarch64-linux-gnu "
                ARCH_PACKAGES+="qemu-user-static qemu-user"
                TARGET_ARCH="arm64"
            ;;
            "x86_64-w64-mingw32")
                ARCH=x86_64
                ML=manylinux2014_x86_64
                ARCH_PACKAGES+="g++-mingw-w64 "
                TARGET_ARCH="amd64"
                $USE_SUDO dpkg --add-architecture $TARGET_ARCH
            ;;
            "i686-w64-mingw32")
                ARCH=x86
                ML=manylinux2014_i686
                ARCH_PACKAGES+="g++-mingw-w64 "
                TARGET_ARCH="i386"
                $USE_SUDO dpkg --add-architecture $TARGET_ARCH
            ;;
            "x86_64-apple-darwin14")
                ARCH=x86_64
                ML=manylinux2014_x86_64
            ;;
            "x86_64-pc-linux-gnu")
                ARCH=x86_64
                ML="manylinux2014_x86_64"
            ;;
            "i686-pc-linux-gnu")
                ARCH=i686
                ML=manylinux2014_i686
                ARCH_PACKAGES+="g++-multilib "
                TARGET_ARCH="i386"
                $USE_SUDO dpkg --add-architecture $TARGET_ARCH
            ;;
            "all")
                ALL_HOST_TRIPLETS=("x86_64-pc-linux-gnu" "i686-pc-linux-gnu" "aarch64-linux-gnu" "arm-linux-gnueabihf" "x86_64-apple-darwin14" "x86_64-w64-mingw32" "i686-w64-mingw32")
            ;;
            *)
                ERROR=1
            ;;
        esac
    ;;
    -o=*|--os=*)
        BUILD_PREFIX="${i#*=}"
    ;;
    -p=*|--prefix=*)
        BUILD_PREFIX="${i#*=}"
    ;;
    -t=*|--tag=*)
        TAG="${i#*=}"
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

check_tools python3 python-is-python3 python3-venv curl tar unzip gpg patchelf 

if [ ! "$TAG" ]; then
    TAG=0.1.0
fi

reset="\033[0m"
red="\033[31m"
green="\033[32m"
ARCHIVE=""
FILE="libdogecoin-$TAG-"
EXTENSION=".tar.gz"
CHECKSUMS="SHA256SUMS.asc"
URL=https://github.com/dogecoinfoundation/libdogecoin/releases/download/v0.1.0/
if [[ "$ALL_HOST_TRIPLETS" != "" ]]; then
    END=$((${#ALL_HOST_TRIPLETS[@]} - 1))
    curl -L -O $URL$CHECKSUMS
    curl https://raw.githubusercontent.com/dogecoinfoundation/libdogecoin/main/contrib/signing-keys/xanimo-key.pgp | gpg --import
    check_sig $CHECKSUMS
    for i in "${!ALL_HOST_TRIPLETS[@]}"
    do
    :
        TARGET_HOST_TRIPLET="${ALL_HOST_TRIPLETS[$i]}"
        BUILD_PREFIX="`pwd`/lib"
        echo $BUILD_PREFIX
        SIG_STATUS=""
        if [ ! -d "$BUILD_PREFIX" ]; then
            mkdir -p $BUILD_PREFIX
        fi
        if [ ! -d "include" ]; then
            mkdir -p include
        fi
        if [[ "$TARGET_HOST_TRIPLET" == *-mingw32 ]]; then
            EXTENSION=".zip"
            ARCHIVE="$FILE$TARGET_HOST_TRIPLET$EXTENSION"
            curl -L -O "$URL$ARCHIVE"
            SIG_STATUS=$(grep "$ARCHIVE" "$CHECKSUMS" | sha256sum -c | grep OK)
            if [ "$SIG_STATUS" == "$ARCHIVE: OK" ]; then
                printf "$green> checksum looks good$reset\n"
            else
                printf "$red> checksum for this libdogecoin release is invalid! This is BAD and may mean the release has been tampered with. It is strongly recommended that you report this to the libdogecoin developers.$reset\n"
                exit 1;
            fi
            unzip -j "$FILE$TARGET_HOST_TRIPLET$EXTENSION" "$FILE$TARGET_HOST_TRIPLET/lib/libdogecoin.a" "$FILE$TARGET_HOST_TRIPLET/include/libdogecoin.h" -d $BUILD_PREFIX
            unzip -j "$FILE$TARGET_HOST_TRIPLET$EXTENSION"  "$FILE$TARGET_HOST_TRIPLET/include/libdogecoin.h" -d include
            rm $ARCHIVE
        else
            ARCHIVE=$FILE$TARGET_HOST_TRIPLET$EXTENSION
            curl -L -O "$URL$ARCHIVE"
            SIG_STATUS=$(grep "$ARCHIVE" "$CHECKSUMS" | sha256sum -c | grep OK)
            if [ "$SIG_STATUS" == "$ARCHIVE: OK" ]; then
                printf "$green> checksum looks good$reset\n"
            else
                printf "$red> checksum for this libdogecoin release is invalid! This is BAD and may mean the release has been tampered with. It is strongly recommended that you report this to the libdogecoin developers.$reset\n"
                exit 1;
            fi
            tar xvf $ARCHIVE "$FILE$TARGET_HOST_TRIPLET/lib/libdogecoin.a"
            tar xvf $ARCHIVE "$FILE$TARGET_HOST_TRIPLET/include/libdogecoin.h"
            mv $FILE$TARGET_HOST_TRIPLET/lib/libdogecoin.a `pwd`/lib/
            mv $FILE$TARGET_HOST_TRIPLET/include/libdogecoin.h `pwd`/include/
            rm -rf $FILE$TARGET_HOST_TRIPLET*
        fi

    done
    rm $CHECKSUMS
fi

DIST_WHEEL=`find . -maxdepth 2 -type f -regex ".*libdogecoin-.*$ARCH.whl"`
python3 -m pip install --upgrade pip pytest auditwheel cython setuptools wheel build
python3 -m build -w && auditwheel repair --plat $ML dist/libdogecoin-$TAG-cp*-cp*-linux_$ARCH.whl -w ./wheels

rm -rf .venv .pytest_cache __pycache__ libdogecoin-*.egg-info/ libdogecoin-* dist/ build/ *.whl *.so *.c lib/ include/ *.egg-info/

# echo "usage: ./easy_windows.sh <version_no> <abs_path_to_libdogecoin> <abs_path_to_current>"
# (
# cd $2 ;
# rm -rf dist 2> /dev/null;
# rm -rf build 2> /dev/null;
# rm -rf wheelhouse 2> /dev/null;
# rm wrappers/python/libdogecoin/libdogecoin.c 2> /dev/null;
# rm wrappers/python/libdogecoin/libdogecoin.o 2> /dev/null;
# echo "done removing files..." ;
# cd $3 ;
# python3 setup.py --version $1 --path $2 sdist bdist_wheel #&&
# # mv dist/[name on windows].whl wheels/
# )


# echo "usage: ./easy_mac.sh <version_no> <abs_path_to_libdogecoin> <abs_path_to_current>"
# (
# cd $2 ;
# rm -rf dist 2> /dev/null;
# rm -rf build 2> /dev/null;
# rm -rf wheelhouse 2> /dev/null;
# rm wrappers/python/libdogecoin/libdogecoin.c 2> /dev/null;
# rm wrappers/python/libdogecoin/libdogecoin.o 2> /dev/null;
# echo done removing files...\n ;
# cd $3 ;
# python3 setup.py --version $1 --path $2 sdist bdist_wheel &&
# mv dist/libdogecoin-$1-cp39-cp39-macosx_12_0_x86_64.whl wheels/
# )
# echo "usage: ./easy_linux.sh <version_no> <abs_path_to_libdogecoin> <abs_path_to_current>"
# (
# cd $2 ;
# rm -rf dist 2> /dev/null;
# rm -rf build 2> /dev/null;
# rm -rf wheelhouse 2> /dev/null;
# rm wrappers/python/libdogecoin/libdogecoin.c 2> /dev/null;
# rm wrappers/python/libdogecoin/libdogecoin.o 2> /dev/null;
# rm libdogecoin-$1-cp38-cp38-linux_x86_64.whl 2> /dev/null;
# echo "done removing files..." ;
# cd $3 ;
# python3 setup.py --version $1 --path $2 sdist bdist_wheel &&
# auditwheel repair --plat manylinux2014_x86_64 dist/libdogecoin-$1-cp38-cp38-linux_x86_64.whl -w ./wheels
# )
