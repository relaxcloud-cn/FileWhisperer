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
    python3-pip \
    bison \
    libx11-dev \
    libxft-dev \
    libxext-dev \
    libssl-dev \
    libcap-dev \
    libsystemd-dev \
    liblz4-dev \
    libzstd-dev \
    liblzma-dev \
    libgles2-mesa-dev \
    meson \ 
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone https://github.com/Microsoft/vcpkg.git && \
    ./vcpkg/bootstrap-vcpkg.sh

ENV PATH="/opt/vcpkg:${PATH}"
ENV VCPKG_ROOT=/opt/vcpkg

WORKDIR /app
COPY . .

RUN cd fixtures && tar -zxvf file-5.45.tar.gz && cd file-5.45 && ./configure --prefix=/usr && make && make install

WORKDIR /app

RUN cmake -B build -S . --preset=vcpkg
RUN cmake --build build