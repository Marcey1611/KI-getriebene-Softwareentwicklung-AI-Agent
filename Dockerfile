FROM python:3.12-slim

RUN apt-get update && rm -rf /var/lib/apt/lists/*

RUN python -m ensurepip --upgrade
RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

CMD ["bash"]