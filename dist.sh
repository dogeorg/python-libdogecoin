#!/bin/bash
export LC_ALL=C
set -e -o pipefail

if [ $# -eq 0 ]; then
    echo "No arguments provided"
    exit 1
fi

FLAVOR=""
ALL_HOST_TRIPLETS=""
TARGET_HOST_TRIPLET=""
for i in "$@"
do
case $i in
    -h=*|--host=*)
        HOST="${i#*=}"
        TARGET_HOST_TRIPLET=($HOST)
        case "$TARGET_HOST_TRIPLET" in
            "arm-linux-gnueabihf")
                OS=linux
                TARGET_ARCH="arm32v7"
            ;;
            "aarch64-linux-gnu")
                OS=linux
                TARGET_ARCH="arm64v8"
            ;;
            "x86_64-w64-mingw32")
                OS=linux
                TARGET_ARCH="amd64"
            ;;
            "i686-w64-mingw32")
                OS=windows
                TARGET_ARCH="i386"
            ;;
            "x86_64-apple-darwin14")
                OS=darwin
                TARGET_ARCH="amd64"
            ;;
            "x86_64-pc-linux-gnu")
                OS=linux
                TARGET_ARCH="amd64"
            ;;
            "i686-pc-linux-gnu")
                OS=linux
                TARGET_ARCH="i386"
            ;;
            *)
                ERROR=1
            ;;
        esac
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

if [ "$OS" == "windows" ]; then
    
fi

docker buildx build \
-t xanimo/python-libdogecoin:$TARGET_ARCH \
--build-arg FLAVOR=${FLAVOR:-"bullseye"} \
--build-arg ARCH=$TARGET_ARCH \
--build-arg TARGET_HOST=$TARGET_HOST_TRIPLET \
--target artifact \
--output type=local,dest=. .