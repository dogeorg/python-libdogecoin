# syntax=docker/dockerfile:1
ARG FLAVOR=${FLAVOR:-"bullseye"}
ARG ARCH=${ARCH:-"amd64"}

FROM $ARCH/python:$FLAVOR AS build
ARG TARGET_HOST=${TARGET_HOST:-"x86_64-pc-linux-gnu"}

COPY . /work
WORKDIR /work

RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf automake libtool \
    build-essential \
    curl tar unzip gpg \
    patchelf \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip cffi setuptools wheel build requests auditwheel pytest

RUN python fetch.py --host=${TARGET_HOST}

RUN python -m build -w && \
    case "${TARGET_HOST}" in \
      "arm-linux-gnueabihf") ML="manylinux2014_armv7l" ;; \
      "aarch64-linux-gnu")   ML="manylinux2014_aarch64" ;; \
      "x86_64-pc-linux-gnu") ML="manylinux2014_x86_64" ;; \
      "i686-pc-linux-gnu")   ML="manylinux2014_i686" ;; \
    esac && \
    TARGET_WHEEL=$(find ./dist -name "*.whl") && \
    python -m auditwheel repair --plat "${ML}" "${TARGET_WHEEL}" -w ./wheels && \
    rm -rf ./dist

RUN TARGET_WHEEL=$(find ./wheels -name "*.whl") && \
    python -m wheel unpack "${TARGET_WHEEL}" && \
    cp -r ./tests ./libdogecoin-0.1.1/ && \
    cd ./libdogecoin-0.1.1 && \
    python -m pytest

FROM scratch AS artifact
COPY --from=build /work/wheels ./wheels
