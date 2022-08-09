# syntax=docker/dockerfile:1
ARG FLAVOR=${FLAVOR:-"bullseye"}
ARG ARCH=${ARCH:-"amd64"}

FROM $ARCH/python:$FLAVOR AS build
ARG TARGET_HOST=${TARGET_HOST:-"x86_64-pc-linux-gnu"}

RUN mkdir -p work/wheels
COPY . /work
WORKDIR /work
RUN if [[ "TARGET_HOST" == "*-mingw32" ]]; then \
    python3 -m fetch.py --host $TARGET_HOST; else \
    ./build.sh --host=$TARGET_HOST &&  ./test.sh; fi

FROM scratch as artifact
COPY --from=build /work/wheels /wheels

FROM release
