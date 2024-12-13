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
    linux-libc-dev \
    autoconf \
    automake \
    autoconf-archive \
    libtool \
    g++ \
    gcc \
    python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone https://github.com/Microsoft/vcpkg.git && \
    ./vcpkg/bootstrap-vcpkg.sh

ENV PATH="/opt/vcpkg:${PATH}"
ENV VCPKG_ROOT=/opt/vcpkg

ENV VCPKG_DEFAULT_LIBRARY_TYPE=dynamic

WORKDIR /app
COPY . .

RUN cd fixtures && tar -zxvf file-5.45.tar.gz && cd file-5.45 && ./configure --prefix=/usr && make && make install

WORKDIR /app

RUN vcpkg install icu:x64-linux

RUN cmake -B build -S . --preset=vcpkg
RUN cmake --build build