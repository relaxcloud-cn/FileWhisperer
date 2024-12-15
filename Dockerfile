FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/vcpkg:${PATH}"
ENV VCPKG_ROOT=/opt/vcpkg
ENV VCPKG_MAX_CONCURRENCY=$(nproc)

RUN apt-get update && apt-get install -y \
    autoconf \
    autoconf-archive \
    automake \
    bison \
    build-essential \
    cmake \
    curl \
    g++ \
    gcc \
    git \
    libcap-dev \
    libgles2-mesa-dev \
    liblz4-dev \
    liblzma-dev \
    libssl-dev \
    libx11-dev \
    libxext-dev \
    libxft-dev \
    libzstd-dev \
    linux-libc-dev \
    meson \
    ninja-build \
    pkg-config \
    python3 \
    python3-pip \
    tar \
    unzip \
    zip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone --depth 1 https://github.com/Microsoft/vcpkg.git && \
    ./vcpkg/bootstrap-vcpkg.sh

WORKDIR /app
COPY vcpkg.json .

RUN if [ -f vcpkg.json ]; then \
    vcpkg install --jobs=$(nproc) \
    --clean-after-build \
    --no-print-usage \
    ; fi

COPY . .

RUN cd fixtures && \
    tar -zxf file-5.45.tar.gz && \
    cd file-5.45 && \
    ./configure --prefix=/usr && \
    make -j$(nproc) && \
    make install

RUN cmake -B build -S . --preset=vcpkg -DCMAKE_BUILD_TYPE=Release || ( \
    cat /opt/vcpkg/buildtrees/libsystemd/config-x64-linux-dbg-meson-log.txt.log && \
    cat /opt/vcpkg/buildtrees/libsystemd/config-x64-linux-dbg-out.log && \
    false )
RUN cmake --build build -j$(nproc)