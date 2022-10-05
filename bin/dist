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
            TARGET_ARCH="arm32v7"
        ;;
        "aarch64-linux-gnu")
            OS=linux
            TARGET_ARCH="arm64v8"
        ;;
        "x86_64-pc-linux-gnu")
            OS=linux
            TARGET_ARCH="amd64"
        ;;
        "i686-pc-linux-gnu")
            OS=linux
            TARGET_ARCH="i386"
        ;;
        "all")
            ALL_HOST_TRIPLETS=("x86_64-pc-linux-gnu" "i686-pc-linux-gnu" "aarch64-linux-gnu" "arm-linux-gnueabihf")
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
    # if [ ! -f "$PWD/logs/$TARGET_HOST_TRIPLET-build-log.txt" ]; then
    #     touch $PWD/logs/$TARGET_HOST_TRIPLET-build-log.txt
    # fi

    docker buildx build \
    -t xanimo/python-libdogecoin:$TARGET_ARCH \
    --build-arg FLAVOR=${FLAVOR:-"bullseye"} \
    --build-arg ARCH=$TARGET_ARCH \
    --build-arg TARGET_HOST=$TARGET_HOST_TRIPLET \
    --target artifact \
    --output type=local,dest=. .
    #  \
    # 2> $PWD/logs/$TARGET_HOST_TRIPLET-build-log.txt \
    # > >(tail -f $PWD/logs/$TARGET_HOST_TRIPLET-build-log.txt)
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
