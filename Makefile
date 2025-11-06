.PHONY: help deploy-agent-engine deploy-bq-agent-mick deploy-bq-agent deploy-all-agents deploy-cloud-run deploy-web deploy-web-simple deploy-web-automated security-harden configure-auth verify-deployment deploy test-local setup check-prereqs clean lint format clean-all config info create-staging-bucket enable-apis test-adk-cli generate-service grant-bq-permissions list-deployments cleanup-deployments

# Default target
.DEFAULT_GOAL := help

# Variables
PROJECT_ID ?= $(shell echo $$(gcloud config get-value project 2>/dev/null || echo ""))
LOCATION ?= us-central1
AGENT_NAME ?= bq_agent_mick
AGENT_DIR ?= bq_agent_mick
STAGING_BUCKET ?= $(PROJECT_ID)-agent-engine-staging
SERVICE_NAME ?= bq-agent-mick
KEEP ?= 1
CLEANUP_BEFORE ?= 
NO_CLEANUP ?=

# Agent directories that can be deployed
AGENT_DIRS = bq_agent_mick bq_agent

# Python version - Agent Engine supports 3.9, 3.10, 3.11, 3.12, 3.13
# Prefer virtual environment Python if it exists, otherwise try to find a supported version
PYTHON ?= $(shell \
	if [ -f .venv/bin/python ]; then \
		echo .venv/bin/python; \
	elif command -v python3.13 >/dev/null 2>&1; then \
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
	@echo "  $(COLOR_YELLOW)AGENT_NAME$(COLOR_RESET)       = $(AGENT_NAME) (for deploy-agent-engine)"
	@echo "  $(COLOR_YELLOW)AGENT_DIR$(COLOR_RESET)        = $(AGENT_DIR) (for deploy-agent-engine)"
	@echo "  $(COLOR_YELLOW)STAGING_BUCKET$(COLOR_RESET)   = $(STAGING_BUCKET)"
	@echo "  $(COLOR_YELLOW)SERVICE_NAME$(COLOR_RESET)     = $(SERVICE_NAME)"
	@PYTHON_VERSION=$$($(PYTHON) --version 2>&1 | cut -d' ' -f2 2>/dev/null || echo "unknown"); \
	echo "  $(COLOR_YELLOW)PYTHON$(COLOR_RESET)            = $(PYTHON) ($$PYTHON_VERSION)"
	@echo ""
	@echo "$(COLOR_BOLD)Available Agents:$(COLOR_RESET)"
	@echo "  $(COLOR_CYAN)bq_agent_mick$(COLOR_RESET)      - BigQuery agent (alternative implementation)"
	@echo "  $(COLOR_CYAN)bq_agent$(COLOR_RESET)           - BigQuery agent (production-ready)"
	@echo ""
	@echo "$(COLOR_BOLD)Examples:$(COLOR_RESET)"
	@echo "  make deploy-bq-agent-mick PROJECT_ID=my-project"
	@echo "  make deploy-bq-agent"
	@echo "  make deploy-all-agents"
	@echo "  make deploy-agent-engine AGENT_DIR=bq_agent"
	@echo "  make deploy-cloud-run LOCATION=us-west1"
	@echo "  make deploy-web-simple PROJECT_ID=my-project"
	@echo "  make deploy-web-automated PROJECT_ID=my-project ACCESS_CONTROL_TYPE=domain ACCESS_CONTROL_VALUE=asl.apps-eval.com"
	@echo "  make security-harden PROJECT_ID=my-project ACCESS_CONTROL_TYPE=domain ACCESS_CONTROL_VALUE=asl.apps-eval.com"
	@echo "  make configure-auth PROJECT_ID=my-project"
	@echo "  make verify-deployment PROJECT_ID=my-project"
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

deploy-agent-engine: check-prereqs ## Deploy specified agent to Vertex AI Agent Engine (use AGENT_DIR variable). Automatically cleans up old deployments after deployment (keeps latest 1, like Cloud Run). Use KEEP=N to keep N deployments, NO_CLEANUP=1 to skip cleanup, or CLEANUP_BEFORE=1 to cleanup before deploying.
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		echo "  Set it with: export PROJECT_ID=your-project"; \
		echo "  Or override: make deploy-agent-engine PROJECT_ID=your-project AGENT_DIR=bq_agent"; \
		exit 1; \
	fi
	@if [ ! -d "$(AGENT_DIR)" ]; then \
		echo "✗ Error: Agent directory not found: $(AGENT_DIR)"; \
		echo "  Available agents: $(AGENT_DIRS)"; \
		exit 1; \
	fi
	@PYTHON_VERSION=$$($(PYTHON) --version 2>&1 | cut -d' ' -f2); \
	echo "Deploying $(AGENT_NAME) ($(AGENT_DIR)) to Vertex AI Agent Engine..."; \
	echo "Using $(PYTHON) ($$PYTHON_VERSION)"; \
	echo "Project: $(PROJECT_ID)"; \
	echo "Location: $(LOCATION)"; \
	echo "Staging bucket: $(STAGING_BUCKET)"; \
	echo "Keeping latest deployments: $(KEEP)"; \
	$(PYTHON) scripts/deploy_agent_engine.py \
		--agent-dir $(AGENT_DIR) \
		--project $(PROJECT_ID) \
		--location $(LOCATION) \
		--agent-name $(AGENT_NAME) \
		--staging-bucket $(STAGING_BUCKET) \
		--keep $(KEEP) \
		$(if $(CLEANUP_BEFORE),--cleanup-before) \
		$(if $(NO_CLEANUP),--no-cleanup)

deploy-bq-agent-mick: check-prereqs ## Deploy bq_agent_mick to Vertex AI Agent Engine
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		echo "  Set it with: export PROJECT_ID=your-project"; \
		exit 1; \
	fi
	@$(MAKE) deploy-agent-engine AGENT_DIR=bq_agent_mick AGENT_NAME=bq_agent_mick

deploy-bq-agent: check-prereqs ## Deploy bq_agent to Vertex AI Agent Engine
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		echo "  Set it with: export PROJECT_ID=your-project"; \
		exit 1; \
	fi
	@$(MAKE) deploy-agent-engine AGENT_DIR=bq_agent AGENT_NAME=bq_agent

deploy-all-agents: check-prereqs ## Deploy all agents to Vertex AI Agent Engine
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		echo "  Set it with: export PROJECT_ID=your-project"; \
		exit 1; \
	fi
	@echo "Deploying all agents to Vertex AI Agent Engine..."
	@echo "Agents: $(AGENT_DIRS)"
	@echo ""
	@for agent_dir in $(AGENT_DIRS); do \
		echo "============================================================"; \
		echo "Deploying $$agent_dir..."; \
		echo "============================================================"; \
		$(MAKE) deploy-agent-engine AGENT_DIR=$$agent_dir AGENT_NAME=$$agent_dir || exit 1; \
		echo ""; \
	done
	@echo "✓ All agents deployed successfully!"

list-deployments: ## List all Agent Engine deployments
	@if [ -z "$(PROJECT_ID)" ]; then \
		PROJECT_ID=$$(gcloud config get-value project 2>/dev/null || echo ""); \
		if [ -z "$$PROJECT_ID" ]; then \
			echo "✗ Error: PROJECT_ID must be set"; \
			exit 1; \
		fi; \
	fi; \
	$(PYTHON) scripts/list_agent_engines.py \
		--project $(PROJECT_ID) \
		--location $(LOCATION) \
		$(if $(AGENT_NAME),--filter-name $(AGENT_NAME),)

cleanup-deployments: ## Clean up old Agent Engine deployments (use AGENT_NAME and KEEP variables). Use FORCE=1 to force delete deployments with active sessions.
	@if [ -z "$(PROJECT_ID)" ]; then \
		PROJECT_ID=$$(gcloud config get-value project 2>/dev/null || echo ""); \
		if [ -z "$$PROJECT_ID" ]; then \
			echo "✗ Error: PROJECT_ID must be set"; \
			exit 1; \
		fi; \
	fi
	@if [ -z "$(AGENT_NAME)" ]; then \
		echo "✗ Error: AGENT_NAME must be set"; \
		echo "  Example: make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1"; \
		exit 1; \
	fi
	@KEEP=$${KEEP:-1}; \
	$(PYTHON) scripts/cleanup_old_deployments.py \
		--agent-name $(AGENT_NAME) \
		--project $(PROJECT_ID) \
		--location $(LOCATION) \
		--keep $$KEEP \
		$(if $(DRY_RUN),--dry-run,) \
		$(if $(FORCE),--force,)

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

deploy-web-simple: check-prereqs ## Deploy web application (backend + frontend) to Cloud Run with Firestore authentication. Use SKIP_CONFIRM=1 to skip confirmation prompt.
	@if [ -z "$(PROJECT_ID)" ]; then \
		PROJECT_ID=$$(gcloud config get-value project 2>/dev/null || echo ""); \
		if [ -z "$$PROJECT_ID" ]; then \
			echo "✗ Error: PROJECT_ID must be set"; \
			echo "  Set it with: export PROJECT_ID=your-project"; \
			echo "  Or override: make deploy-web-cloud-run PROJECT_ID=your-project"; \
			exit 1; \
		fi; \
	fi
	@echo "Deploying web application to Cloud Run with Firestore authentication..."
	@echo "Project: $(PROJECT_ID)"
	@echo "Region: $(LOCATION)"
	@echo ""
	@cd web/deploy && \
		export PROJECT_ID="$(PROJECT_ID)" && \
		export REGION="$(LOCATION)" && \
		if [ "$(SKIP_CONFIRM)" = "1" ] || [ "$(SKIP_CONFIRM)" = "true" ]; then \
			./deploy-simple-iap.sh -y; \
		else \
			./deploy-simple-iap.sh; \
		fi


deploy-web: ## Show help for web deployments
	@echo "$(COLOR_BOLD)Web Deployment Options:$(COLOR_RESET)"
	@echo "  $(COLOR_CYAN)make deploy-web-simple$(COLOR_RESET)    - Deploy to Cloud Run with Firestore authentication (simple, no load balancer)"

deploy-web-automated: check-prereqs ## Fully automated deployment: infrastructure, IAM, security, apps. Use ACCESS_CONTROL_TYPE=domain ACCESS_CONTROL_VALUE=asl.apps-eval.com
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		echo "  Set it with: export PROJECT_ID=your-project"; \
		echo "  Example: make deploy-all-automated PROJECT_ID=my-project ACCESS_CONTROL_TYPE=domain ACCESS_CONTROL_VALUE=innovationbox.cloud"; \
		exit 1; \
	fi
	@echo "🚀 Starting fully automated deployment..."
	@cd web/deploy && \
		export PROJECT_ID="$(PROJECT_ID)" && \
		export REGION="$(LOCATION)" && \
		export DOMAIN="$(DOMAIN)" && \
		export ACCESS_CONTROL_TYPE="$(ACCESS_CONTROL_TYPE)" && \
		export ACCESS_CONTROL_VALUE="$(ACCESS_CONTROL_VALUE)" && \
		export FIREBASE_API_KEY="$(FIREBASE_API_KEY)" && \
		export FIREBASE_AUTH_DOMAIN="$(FIREBASE_AUTH_DOMAIN)" && \
		export FIREBASE_PROJECT_ID="$(FIREBASE_PROJECT_ID)" && \
		export FIREBASE_STORAGE_BUCKET="$(FIREBASE_STORAGE_BUCKET)" && \
		export FIREBASE_MESSAGING_SENDER_ID="$(FIREBASE_MESSAGING_SENDER_ID)" && \
		export FIREBASE_APP_ID="$(FIREBASE_APP_ID)" && \
		if [ "$(SKIP_CONFIRM)" = "1" ] || [ "$(SKIP_CONFIRM)" = "true" ]; then \
			./deploy-all-automated.sh -y; \
		else \
			./deploy-all-automated.sh; \
		fi

security-harden: check-prereqs ## Apply security hardening: replace allAuthenticatedUsers with domain/group/user restrictions. Use ACCESS_CONTROL_TYPE=domain ACCESS_CONTROL_VALUE=asl.apps-eval.com
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		echo "  Set it with: export PROJECT_ID=your-project"; \
		echo "  Example: make security-harden PROJECT_ID=my-project ACCESS_CONTROL_TYPE=domain ACCESS_CONTROL_VALUE=innovationbox.cloud"; \
		exit 1; \
	fi
	@echo "🔐 Applying security hardening..."
	@echo "Project: $(PROJECT_ID)"
	@echo "Region: $(LOCATION)"
	@echo "Access Control Type: $(ACCESS_CONTROL_TYPE)"
	@echo "Access Control Value: $(ACCESS_CONTROL_VALUE)"
	@echo ""
	@cd web/deploy && \
		export PROJECT_ID="$(PROJECT_ID)" && \
		export REGION="$(LOCATION)" && \
		export ACCESS_CONTROL_TYPE="$(ACCESS_CONTROL_TYPE)" && \
		export ACCESS_CONTROL_VALUE="$(ACCESS_CONTROL_VALUE)" && \
		./05-security-hardening.sh

configure-auth: check-prereqs ## Configure authentication (OAuth, IAP APIs). Note: OAuth consent screen requires manual setup.
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		echo "  Set it with: export PROJECT_ID=your-project"; \
		echo "  Example: make configure-auth PROJECT_ID=my-project"; \
		exit 1; \
	fi
	@echo "🔐 Configuring authentication..."
	@cd web/deploy && \
		export PROJECT_ID="$(PROJECT_ID)" && \
		export REGION="$(LOCATION)" && \
		$(if $(SKIP_CONFIRM),export SKIP_CONFIRM=1 &&) \
		./06-configure-authentication.sh $(if $(SKIP_CONFIRM),-y,)

verify-deployment: check-prereqs ## Verify deployment: check all components are correctly deployed and configured
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "✗ Error: PROJECT_ID must be set"; \
		echo "  Set it with: export PROJECT_ID=your-project"; \
		echo "  Example: make verify-deployment PROJECT_ID=my-project"; \
		exit 1; \
	fi
	@echo "🔍 Verifying deployment..."
	@cd web/deploy && \
		export PROJECT_ID="$(PROJECT_ID)" && \
		export REGION="$(LOCATION)" && \
		export DOMAIN="$(DOMAIN)" && \
		./verify-deployment.sh

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
	@echo "  2. Web Application Deployment"
	@echo "     Run: $(COLOR_CYAN)make deploy-web$(COLOR_RESET) to see options (simple or automated)"
	@echo ""
	@echo "  3. Cloud Run (alternative deployment option for agents)"
	@echo "     Run: $(COLOR_CYAN)make deploy-cloud-run$(COLOR_RESET)"
	@echo "     (Requires service.py - run 'make generate-service' first)"
	@echo ""
	@echo "  4. Local testing"
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
