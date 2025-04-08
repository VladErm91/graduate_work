FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей для сборки и git
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libopenblas-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Установка зависимостей без lightfm
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install git+https://github.com/daviddavo/lightfm.git#egg=lightfm

COPY . .
