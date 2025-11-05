.PHONY: help deploy-agent-engine deploy-cloud-run deploy test-local setup check-prereqs clean lint format clean-all config info create-staging-bucket enable-apis test-adk-cli generate-service grant-bq-permissions

# Default target
.DEFAULT_GOAL := help

# Variables
PROJECT_ID ?= $(shell echo $$(gcloud config get-value project 2>/dev/null || echo ""))
LOCATION ?= us-central1
AGENT_NAME ?= bq_agent_mick
AGENT_DIR ?= bq_agent_mick
STAGING_BUCKET ?= $(PROJECT_ID)-agent-engine-staging
SERVICE_NAME ?= bq-agent-mick

# Python version - Agent Engine supports 3.9, 3.10, 3.11, 3.12, 3.13
# Try to find a supported version, defaulting to python3.13 if available
PYTHON ?= $(shell \
	if command -v python3.13 >/dev/null 2>&1; then \
		echo python3.13; \
	elif command -v python3.12 >/dev/null 2>&1; then \
		echo python3.12; \
	elif command -v python3.11 >/dev/null 2>&1; then \
		echo python3.11; \
	elif command -v python3.10 >/dev/null 2>&1; then \
		echo python3.10; \
	elif command -v python3.9 >/dev/null 2>&1; then \
		echo python3.9; \
	else \
		echo python3; \
	fi)

# Colors for help output
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_YELLOW := \033[33m
COLOR_CYAN := \033[36m

help: ## Show this help message
	@echo "$(COLOR_BOLD)Available commands:$(COLOR_RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_CYAN)%-25s$(COLOR_RESET) %s\n", $$1, $$2}' | \
		sort
	@echo ""
	@echo "$(COLOR_BOLD)Variables (can be overridden):$(COLOR_RESET)"
	@echo "  $(COLOR_YELLOW)PROJECT_ID$(COLOR_RESET)       = $(PROJECT_ID)"
	@echo "  $(COLOR_YELLOW)LOCATION$(COLOR_RESET)         = $(LOCATION)"
	@echo "  $(COLOR_YELLOW)AGENT_NAME$(COLOR_RESET)       = $(AGENT_NAME)"
	@echo "  $(COLOR_YELLOW)STAGING_BUCKET$(COLOR_RESET)   = $(STAGING_BUCKET)"
	@echo "  $(COLOR_YELLOW)SERVICE_NAME$(COLOR_RESET)     = $(SERVICE_NAME)"
	@PYTHON_VERSION=$$($(PYTHON) --version 2>&1 | cut -d' ' -f2 2>/dev/null || echo "unknown"); \
	echo "  $(COLOR_YELLOW)PYTHON$(COLOR_RESET)            = $(PYTHON) ($$PYTHON_VERSION)"
	@echo ""
	@echo "$(COLOR_BOLD)Examples:$(COLOR_RESET)"
	@echo "  make deploy-agent-engine PROJECT_ID=my-project"
	@echo "  make deploy PYTHON=python3.13"
	@echo "  make deploy-cloud-run LOCATION=us-west1"
	@echo "  make test-local"

check-prereqs: ## Check if required tools and dependencies are installed
	@echo "Checking prerequisites..."
	@PYTHON_VERSION=$$($(PYTHON) --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2); \
	if [ -z "$$PYTHON_VERSION" ]; then \
		echo "✗ $(PYTHON) not found or cannot get version"; \
		exit 1; \
	fi; \
	echo "✓ Using $(PYTHON) (version $$PYTHON_VERSION)"; \
	MAJOR=$$(echo $$PYTHON_VERSION | cut -d'.' -f1); \
	MINOR=$$(echo $$PYTHON_VERSION | cut -d'.' -f2); \
	if [ "$$MAJOR" != "3" ] || [ $$MINOR -lt 9 ] || [ $$MINOR -gt 13 ]; then \
		echo "⚠ Warning: Python $$PYTHON_VERSION may not be supported by Agent Engine"; \
		echo "  Agent Engine supports Python 3.9, 3.10, 3.11, 3.12, 3.13"; \
		echo "  Override with: make deploy PYTHON=python3.13"; \
	fi
	@command -v adk >/dev/null 2>&1 || { echo "✗ adk CLI not found. Install with: pip install google-adk"; exit 1; }
	@echo "✓ adk CLI found"
	@command -v gcloud >/dev/null 2>&1 || { echo "✗ gcloud CLI not found. Install Google Cloud SDK"; exit 1; }
	@echo "✓ gcloud CLI found"
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "⚠ Warning: PROJECT_ID not set. Set it with: export PROJECT_ID=your-project"; \
		echo "  Or override: make deploy-agent-engine PROJECT_ID=your-project"; \
	fi
	@echo "✓ Prerequisites check complete"

setup: ## Set up the development environment
	@echo "Setting up development environment with $(PYTHON)..."
	$(PYTHON) -m venv .venv || true
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "✓ Setup complete. Activate with: source .venv/bin/activate"
	@echo "  Virtual environment uses: $$(.venv/bin/python --version)"

deploy-agent-engine: check-prereqs ## Deploy agent to Vertex AI Agent Engine
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		echo "  Set it with: export PROJECT_ID=your-project"; \
		echo "  Or override: make deploy-agent-engine PROJECT_ID=your-project"; \
		exit 1; \
	fi
	@PYTHON_VERSION=$$($(PYTHON) --version 2>&1 | cut -d' ' -f2); \
	echo "Deploying $(AGENT_NAME) to Vertex AI Agent Engine..."; \
	echo "Using $(PYTHON) ($$PYTHON_VERSION)"; \
	echo "Project: $(PROJECT_ID)"; \
	echo "Location: $(LOCATION)"; \
	echo "Staging bucket: $(STAGING_BUCKET)"; \
	$(PYTHON) $(AGENT_DIR)/deploy_agent_engine.py \
		--project $(PROJECT_ID) \
		--location $(LOCATION) \
		--agent-name $(AGENT_NAME) \
		--staging-bucket $(STAGING_BUCKET)

deploy-cloud-run: check-prereqs ## Deploy agent as Cloud Run service (requires service.py)
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		exit 1; \
	fi
	@if [ ! -f "$(AGENT_DIR)/service.py" ]; then \
		echo "✗ Error: $(AGENT_DIR)/service.py not found"; \
		echo "  Run 'make generate-service' to create it, or see deploy_vertex_api.py output"; \
		exit 1; \
	fi
	@echo "Deploying $(AGENT_NAME) to Cloud Run..."
	@echo "Project: $(PROJECT_ID)"
	@echo "Location: $(LOCATION)"
	@echo "Service name: $(SERVICE_NAME)"
	gcloud run deploy $(SERVICE_NAME) \
		--source . \
		--platform managed \
		--region $(LOCATION) \
		--project $(PROJECT_ID) \
		--allow-unauthenticated \
		--set-env-vars BQ_PROJECT=$(PROJECT_ID),BQ_DATASET=$(shell grep BQ_DATASET $(AGENT_DIR)/.env 2>/dev/null | cut -d'=' -f2 || echo ""),BQ_LOCATION=$(shell grep BQ_LOCATION $(AGENT_DIR)/.env 2>/dev/null | cut -d'=' -f2 || echo "US")

generate-service: ## Generate Cloud Run service.py file from template
	@echo "Generating $(AGENT_DIR)/service.py..."
	@$(PYTHON) $(AGENT_DIR)/deploy_vertex_api.py --output-config > /dev/null 2>&1 || true
	@echo "Service file template will be shown. Save it manually to $(AGENT_DIR)/service.py"
	@$(PYTHON) -c "import sys; sys.path.insert(0, '.'); \
		from bq_agent_mick.deploy_vertex_api import print_cloud_run_instructions, get_agent_config, create_agent_instructions; \
		import os; \
		config = get_agent_config(); \
		config['instruction'] = create_agent_instructions(config); \
		print_cloud_run_instructions(config, os.getenv('PROJECT_ID', 'your-project'), 'us-central1')" || \
		echo "See deploy_vertex_api.py output for service template"

test-local: ## Test the agent locally
	@echo "Testing agent locally..."
	@echo "Make sure you have activated the virtual environment: source .venv/bin/activate"
	@echo "Then run: $(PYTHON) main.py"
	@echo "Or use ADK CLI: adk run $(AGENT_DIR).agent.root_agent"

test-adk-cli: ## Test agent using ADK CLI
	@echo "Testing agent with ADK CLI..."
	adk run $(AGENT_DIR).agent.root_agent

create-staging-bucket: check-prereqs ## Create GCS staging bucket for Agent Engine deployments
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		exit 1; \
	fi
	@echo "Creating staging bucket: gs://$(STAGING_BUCKET)..."
	@gsutil mb -p $(PROJECT_ID) -l $(LOCATION) gs://$(STAGING_BUCKET) 2>/dev/null || \
		(echo "Bucket already exists or error occurred. Checking..." && \
		 gsutil ls gs://$(STAGING_BUCKET) >/dev/null 2>&1 && \
		 echo "✓ Bucket already exists: gs://$(STAGING_BUCKET)")

enable-apis: check-prereqs ## Enable required Google Cloud APIs
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		exit 1; \
	fi
	@echo "Enabling required APIs for project $(PROJECT_ID)..."
	gcloud services enable aiplatform.googleapis.com --project $(PROJECT_ID)
	gcloud services enable bigquery.googleapis.com --project $(PROJECT_ID)
	gcloud services enable run.googleapis.com --project $(PROJECT_ID)
	gcloud services enable storage-component.googleapis.com --project $(PROJECT_ID)
	@echo "✓ APIs enabled"

lint: ## Run linting checks on Python code
	@echo "Running linting checks..."
	@command -v pylint >/dev/null 2>&1 && pylint $(AGENT_DIR)/*.py || echo "⚠ pylint not installed (optional)"
	@command -v flake8 >/dev/null 2>&1 && flake8 $(AGENT_DIR)/*.py || echo "⚠ flake8 not installed (optional)"
	@echo "✓ Linting complete"

format: ## Format Python code using black (if installed)
	@command -v black >/dev/null 2>&1 && black $(AGENT_DIR)/*.py || echo "⚠ black not installed (optional: pip install black)"

clean: ## Clean generated files and caches
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✓ Clean complete"

clean-all: clean ## Clean everything including virtual environment
	@echo "Removing virtual environment..."
	rm -rf .venv
	@echo "✓ Complete clean done"

config: ## Show current configuration
	@PYTHON_VERSION=$$($(PYTHON) --version 2>&1 | cut -d' ' -f2 2>/dev/null || echo "unknown"); \
	echo "$(COLOR_BOLD)Current Configuration:$(COLOR_RESET)"; \
	echo "  Project ID: $(PROJECT_ID)"; \
	echo "  Location: $(LOCATION)"; \
	echo "  Agent Name: $(AGENT_NAME)"; \
	echo "  Agent Directory: $(AGENT_DIR)"; \
	echo "  Staging Bucket: $(STAGING_BUCKET)"; \
	echo "  Service Name: $(SERVICE_NAME)"; \
	echo "  Python: $(PYTHON) ($$PYTHON_VERSION)"; \
	echo ""; \
	echo "$(COLOR_BOLD)Environment Variables:$(COLOR_RESET)"; \
	env | grep -E "(PROJECT_ID|BQ_PROJECT|BQ_DATASET|BQ_LOCATION|GOOGLE_CLOUD_PROJECT)" || echo "  (none set)"

info: ## Show deployment information and instructions
	@echo "$(COLOR_BOLD)Agent Deployment Information$(COLOR_RESET)"
	@echo ""
	@echo "Available deployment methods:"
	@echo "  1. Vertex AI Agent Engine (recommended for ADK agents)"
	@echo "     Run: $(COLOR_CYAN)make deploy-agent-engine$(COLOR_RESET)"
	@echo ""
	@echo "  2. Cloud Run (alternative deployment option)"
	@echo "     Run: $(COLOR_CYAN)make deploy-cloud-run$(COLOR_RESET)"
	@echo "     (Requires service.py - run 'make generate-service' first)"
	@echo ""
	@echo "  3. Local testing"
	@echo "     Run: $(COLOR_CYAN)make test-local$(COLOR_RESET)"
	@echo ""
	@echo "View detailed deployment docs:"
	@echo "  $(AGENT_DIR)/DEPLOYMENT.md"
	@echo ""
	@echo "View configuration:"
	@echo "  $(COLOR_CYAN)make config$(COLOR_RESET)"

       grant-bq-permissions: check-prereqs ## Grant BigQuery permissions to Agent Engine service accounts
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		exit 1; \
	fi
	@echo "Granting BigQuery permissions to Agent Engine..."
	@$(AGENT_DIR)/grant_permissions.sh

# Quick deployment alias
deploy: deploy-agent-engine ## Alias for deploy-agent-engine (default deployment method)
