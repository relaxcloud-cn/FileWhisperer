FROM nvidia/cuda:12.9.1-cudnn-devel-ubuntu20.04

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install Python 3.11 and dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    curl \
    gcc \
    g++ \
    make \
    tesseract-ocr \
    libtesseract-dev \
    libmagic1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    swig \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.11
RUN curl https://bootstrap.pypa.io/get-pip.py | python3.11

# Set python3.11 as default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/python3.11 1

# Create symlinks for pip
RUN ln -sf /usr/bin/python3.11 /usr/bin/python
RUN python3.11 -m pip install --upgrade pip

COPY requirements.txt .

RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /root/.paddleocr

COPY ocr/whl /root/.paddleocr/whl

COPY . .
