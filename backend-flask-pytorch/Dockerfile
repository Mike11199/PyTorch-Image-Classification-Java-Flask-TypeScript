# Flask/PyTorch backend - uses torch (CPU) + Flask + gunicorn
FROM node:22-bookworm-slim AS javascript
FROM python:3.11-slim
COPY --from=javascript /usr/local/bin/node /usr/local/bin/node

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libglib2.0-0 libsm6 libxrender1 libxext6 libgl1 && \
    rm -rf /var/lib/apt/lists/*

COPY backend-flask-pytorch/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cache pretrained model weights during the image build; ECS task ENIs have no internet path.
ENV TORCH_HOME=/opt/torch-cache
COPY backend-flask-pytorch/prefetch_models.py .
RUN python prefetch_models.py

# Copy app code (includes model loading scripts)
COPY backend-flask-pytorch/. .
COPY frontend/src/assets/ml_video.mp4 /app/examples/ml-video.mp4

EXPOSE 5000

ENV MASK_LOW_RES=true

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
