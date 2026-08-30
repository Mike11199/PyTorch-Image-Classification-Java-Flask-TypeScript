# Flask/PyTorch backend - uses torch (CPU) + Flask + gunicorn
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libglib2.0-0 libsm6 libxrender1 libxext6 && \
    rm -rf /var/lib/apt/lists/*

COPY backend-flask-pytorch/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code (includes model loading scripts)
COPY backend-flask-pytorch/. .

EXPOSE 5000

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
