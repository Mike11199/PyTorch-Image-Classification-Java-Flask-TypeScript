# Flask/PyTorch backend; the local GPU override selects a CUDA build.
FROM node:22-bookworm-slim AS javascript
FROM python:3.11-slim
COPY --from=javascript /usr/local/bin/node /usr/local/bin/node

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libglib2.0-0 libsm6 libxrender1 libxext6 libgl1 && \
    rm -rf /var/lib/apt/lists/*

COPY backend-flask-pytorch/requirements.txt .
ARG TORCH_CUDA=0
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "$TORCH_CUDA" = "1" ]; then \
      sed -e 's/^torch==.*/torch==2.7.0+cu128/' \
          -e 's/^torchvision==.*/torchvision==0.22.0+cu128/' \
          -e 's/^sympy==.*/sympy==1.14.0/' requirements.txt > requirements-cuda.txt && \
      pip install --extra-index-url https://download.pytorch.org/whl/cu128 \
        -r requirements-cuda.txt; \
    else \
      pip install -r requirements.txt; \
    fi

# Cache pretrained model weights during the image build to avoid startup downloads.
ENV TORCH_HOME=/opt/torch-cache
COPY backend-flask-pytorch/prefetch_models.py .
RUN python prefetch_models.py

# Copy app code (includes model loading scripts)
COPY backend-flask-pytorch/. .
COPY frontend/src/assets/ml_video.mp4 /app/examples/ml-video.mp4

EXPOSE 5000

ENV MASK_LOW_RES=true

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
