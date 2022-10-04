# syntax=docker/dockerfile:1
ARG FLAVOR=${FLAVOR:-"bullseye"}
ARG ARCH=${ARCH:-"amd64"}

FROM $ARCH/python:$FLAVOR AS build
ARG TARGET_HOST=${TARGET_HOST:-"x86_64-pc-linux-gnu"}

RUN mkdir -p work/wheels
COPY . /work
WORKDIR /work
RUN ./bin/build --host=$TARGET_HOST --docker

FROM scratch as artifact
COPY --from=build /work/wheels ./wheels

FROM release
