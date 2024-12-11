FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    zip \
    unzip \
    tar \
    git \
    ninja-build \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone https://github.com/Microsoft/vcpkg.git && \
    ./vcpkg/bootstrap-vcpkg.sh

ENV PATH="/opt/vcpkg:${PATH}"

ENV VCPKG_ROOT=/opt/vcpkg

WORKDIR /app

COPY . .

RUN cmake --preset=vcpkg
RUN vcpkg install
RUN cmake --build build
