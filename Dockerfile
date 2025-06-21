FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN python -m ensurepip --upgrade
RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

# FastAPI-Anwendung starten
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]