.PHONY: help dev down logs build ps env

ifeq ($(OS),Windows_NT)
SHELL := cmd.exe
.SHELLFLAGS := /c
endif

help:
	@echo make dev    - Create .env if missing, then build and start containers in the background.
	@echo make down   - Stop and remove containers.
	@echo make logs   - Follow container logs. Press Ctrl+C to exit.
	@echo make build  - Build container images without starting them.
	@echo make ps     - Show container status.
	@echo make env    - Create backend .env from default.env only if missing.
	@echo make help   - Show this command list.

dev: env
	docker compose up --build -d

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
