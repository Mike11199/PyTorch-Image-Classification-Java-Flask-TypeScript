# Build and manage the local Docker services.
.PHONY: help dev dev-gpu dev-cpu down logs build ps env

ifeq ($(OS),Windows_NT)
SHELL := cmd.exe
.SHELLFLAGS := /c
GPU_AVAILABLE := $(shell nvidia-smi -L >NUL 2>NUL && echo yes)
else
GPU_AVAILABLE := $(shell nvidia-smi -L >/dev/null 2>&1 && echo yes)
endif

help:
	@echo make dev     - Build and run locally, using NVIDIA GPU when available.
	@echo make dev-gpu - Force the local Flask container to use the NVIDIA GPU.
	@echo make dev-cpu - Force the local Flask container to use CPU inference.
	@echo make down   - Stop and remove containers.
	@echo make logs   - Follow container logs. Press Ctrl+C to exit.
	@echo make build  - Build container images without starting them.
	@echo make ps     - Show container status.
	@echo make env    - Create backend .env from default.env only if missing.
	@echo make help   - Show this command list.

dev: $(if $(filter yes,$(GPU_AVAILABLE)),dev-gpu,dev-cpu)

dev-gpu: env
	@echo Starting local development with NVIDIA GPU inference.
	docker compose -f compose.yaml -f compose.gpu.yaml up --build -d
	docker compose exec -T flask python -c "import torch; assert torch.cuda.is_available(), 'GPU startup failed: CUDA is unavailable inside Flask'; x = torch.ones(1, device='cuda'); assert x.item() == 1; print('CUDA verified:', torch.cuda.get_device_name(0), 'torch', torch.__version__)"

dev-cpu: env
	@echo Starting local development with CPU inference.
	docker compose -f compose.yaml up --build -d

down: env
	docker compose down

logs: env
	docker compose logs -f

build: env
	docker compose build

ps: env
	docker compose ps

env: backend-flask-pytorch/.env

# This rule creates the backend .env file only if it is missing.
# If .env already exists, Make skips the copy and keeps your settings.
backend-flask-pytorch/.env:
ifeq ($(OS),Windows_NT)
	copy backend-flask-pytorch\default.env backend-flask-pytorch\.env
else
	cp backend-flask-pytorch/default.env backend-flask-pytorch/.env
endif
