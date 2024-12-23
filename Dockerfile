# syntax=docker/dockerfile:1
ARG TARGETARCH

FROM ubuntu:22.04 AS builder

ARG TARGETARCH
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/vcpkg:${PATH}"
ENV VCPKG_ROOT=/opt/vcpkg
ENV VCPKG_DISABLE_METRICS=1
ENV VCPKG_FEATURE_FLAGS=manifests
ENV VCPKG_MAX_CONCURRENCY=8
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

# Set VCPKG triplet based on architecture directly in ENV
ENV VCPKG_TRIPLET=x64-linux
RUN if [ "$TARGETARCH" != "amd64" ]; then \
        echo "Setting VCPKG triplet for $TARGETARCH" && \
        export VCPKG_TRIPLET="${TARGETARCH}-linux" && \
        echo "VCPKG_TRIPLET=$VCPKG_TRIPLET" > /etc/environment && \
        echo "export VCPKG_TRIPLET=$VCPKG_TRIPLET" >> /etc/profile; \
    fi

ENV VCPKG_DEFAULT_TRIPLET=${VCPKG_TRIPLET}
ENV VCPKG_TARGET_TRIPLET=${VCPKG_TRIPLET}
ENV VCPKG_HOST_TRIPLET=${VCPKG_TRIPLET}

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

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
    libtool \
    libcap-dev \
    libgles2-mesa-dev \
    liblz4-dev \
    liblzma-dev \
    libssl-dev \
    libx11-dev \
    libxext-dev \
    libxft-dev \
    libxi-dev \
    libxtst-dev \
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
    python3-jinja2 \
    libdbus-1-dev \
    libgirepository1.0-dev \
    libglib2.0-dev \
    locales \
    libcairo2-dev \
    libpango1.0-dev \
    libatk1.0-dev \
    libgdk-pixbuf2.0-dev \
    libepoxy-dev \
    libxrandr-dev \
    libxkbcommon-dev \
    iso-codes \
    libxcursor-dev \
    libxdamage-dev \
    libxcomposite-dev \
    sassc \
    xsltproc \
    libcups2-dev \
    libxml2-dev \
    libxfixes-dev \
    libxinerama-dev \
    libgtk-3-dev \
    gettext \
    libsystemd-dev \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

WORKDIR /opt
RUN git clone --depth 1 https://github.com/Microsoft/vcpkg.git && \
    ./vcpkg/bootstrap-vcpkg.sh

WORKDIR /app
COPY . .

RUN cd fixtures && \
    tar -zxf file-5.45.tar.gz && \
    cd file-5.45 && \
    ./configure --prefix=/usr/local && \
    make -j$(nproc) && \
    make install

RUN cmake -B build -S . \
    --preset=vcpkg-linux \
    -G "Ninja" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER=/usr/bin/gcc \
    -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
    -DCMAKE_MAKE_PROGRAM=/usr/bin/ninja \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DVCPKG_TARGET_TRIPLET=${VCPKG_TRIPLET} \
    -DVCPKG_HOST_TRIPLET=${VCPKG_TRIPLET} \
    || ( \
        cat build/vcpkg-manifest-install.log || true && \
        false \
    )

RUN cmake --build build -j$(nproc)

FROM ubuntu:22.04

ARG TARGETARCH

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

RUN apt-get update && apt-get install -y locales && \
    locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

WORKDIR /app

COPY --from=builder /app/build /app/build
COPY --from=builder /app/fixtures /app/fixtures