FROM python:3.11-slim

LABEL maintainer="season@maybi.cn"
LABEL description="Bibi - 一站式海外华人购物平台"

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_upgraded.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project code
COPY . /app

# Create upload directories
RUN mkdir -p /app/application/static/csv \
    /app/application/static/img/avatar

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "wsgi:app", "-b", "0.0.0.0:5000", "--timeout", "120", "--access-logfile", "-"]
