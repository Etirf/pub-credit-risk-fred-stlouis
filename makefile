# ============================================
#  Makefile for Credit Risk ML Service
# ============================================

# -------- Colors --------
GREEN  := \033[0;32m
YELLOW := \033[1;33m
CYAN   := \033[0;36m
RESET  := \033[0m

# -------- Default target --------
.DEFAULT_GOAL := help

.PHONY: help install format lint test run worker compose-up compose-down restart clean clean-py

# ============================================
#  HELP
# ============================================

help:
	@echo ""
	@echo "$(CYAN)Credit Risk ML Service — Available Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)make install       $(RESET)- Install all dependencies with uv"
	@echo "$(GREEN)make format        $(RESET)- Auto-fix code style using Ruff"
	@echo "$(GREEN)make lint          $(RESET)- Run Ruff lint checks"
	@echo "$(GREEN)make test          $(RESET)- Run unit + integration tests"
	@echo "$(GREEN)make run           $(RESET)- Start FastAPI development server"
	@echo "$(GREEN)make worker        $(RESET)- Start Celery worker"
	@echo "$(GREEN)make compose-up    $(RESET)- Run full stack (API + worker + Redis + Postgres)"
	@echo "$(GREEN)make compose-down  $(RESET)- Stop stack & remove containers"
	@echo "$(GREEN)make restart       $(RESET)- Rebuild & restart Docker Compose"
	@echo "$(GREEN)make clean         $(RESET)- Remove caches + artifact files"
	@echo ""

# ============================================
#  DEVELOPMENT
# ============================================

install:
	@echo "$(YELLOW)Installing dependencies...$(RESET)"
	uv sync --all-groups

format:
	@echo "$(YELLOW)Formatting code with Ruff...$(RESET)"
	uv run ruff check --fix .
	uv run ruff format .

lint:
	@echo "$(YELLOW)Linting code with Ruff...$(RESET)"
	uv run ruff check .

test:
	@echo "$(YELLOW)Running tests...$(RESET)"
	uv run pytest -q

# ============================================
#  APPLICATION
# ============================================

run:
	@echo "$(GREEN)Starting FastAPI server...$(RESET)"
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	@echo "$(GREEN)Starting Celery worker...$(RESET)"
	uv run celery -A app.artifacts.infrastructure.celery_app worker --loglevel=INFO

# ============================================
#  DOCKER COMPOSE
# ============================================

compose-up:
	@echo "$(GREEN)Starting Docker Compose stack...$(RESET)"
	docker compose up --build

compose-down:
	@echo "$(YELLOW)Stopping Docker Compose stack...$(RESET)"
	docker compose down -v

restart:
	@echo "$(YELLOW)Restarting Docker Compose stack...$(RESET)"
	docker compose down -v
	docker compose up --build

# ============================================
#  CLEANUP
# ============================================

clean-py:
	@echo "$(YELLOW)Removing Python cache files...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

clean: clean-py
	@echo "$(YELLOW)Cleaning artifacts...$(RESET)"
	rm -rf storage/models/*
	rm -rf storage/datasets/*
	rm -rf storage/macro_cache/*
	@echo "$(GREEN)Cleanup complete.$(RESET)"
