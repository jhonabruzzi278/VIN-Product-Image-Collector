FROM python:3.12-slim

WORKDIR /app

# Dependencias de sistema mínimas para Pillow (jpeg/webp) — el resto de las
# dependencias del proyecto son puro Python.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libjpeg62-turbo libwebp7 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./
COPY src ./src

RUN pip install --no-cache-dir -e .

# input/output/cache/database/logs/config se montan como volúmenes en
# docker-compose.yml para persistir datos fuera del contenedor.
COPY config ./config
RUN mkdir -p input output/images output/thumbnails cache logs database

EXPOSE 8000

CMD ["uvicorn", "vin_collector.web:app", "--host", "0.0.0.0", "--port", "8000"]
