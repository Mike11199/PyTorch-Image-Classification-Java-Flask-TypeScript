# Flask/PyTorch backend - uses torch (CPU) + Flask + gunicorn
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libglib2.0-0 libsm6 libxrender1 libxext6 libgl1 && \
    rm -rf /var/lib/apt/lists/*

COPY backend-flask-pytorch/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cache pretrained model weights during the image build; ECS task ENIs have no internet path.
ENV TORCH_HOME=/opt/torch-cache
COPY backend-flask-pytorch/prefetch_models.py .
RUN python prefetch_models.py

# Copy app code (includes model loading scripts)
COPY backend-flask-pytorch/. .

EXPOSE 5000

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
