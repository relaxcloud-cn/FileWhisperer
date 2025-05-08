FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    tesseract-ocr \
    libtesseract-dev \
    libmagic1 \
    libgl1 \
    libglib2.0-0 \
    swig \
    libcudnn8 \
    libcudnn8-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /root/.paddleocr

COPY ocr/whl /root/.paddleocr/whl

COPY . .
