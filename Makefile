.DEFAULT_GOAL := help

VERSION=0.1-dev
PROJECT_REGISTRY=registry.thalesdigital.io/tsn/projects/knowledge_flow_app
PROJECT_NAME=knowledge-flow
PY_PACKAGE=knowledge_flow_app

ROOT_DIR := $(realpath $(CURDIR))
ENV_FILE := $(ROOT_DIR)/config/.env

TARGET=$(CURDIR)/target
VENV=$(CURDIR)/.venv
PIP=$(VENV)/bin/pip
PYTHON=$(VENV)/bin/python
UV=$(VENV)/bin/uv

IMG=$(PROJECT_REGISTRY)/$(PROJECT_NAME):$(VERSION)
HELM_ARCHIVE=./knowledge_flow_app-0.1.0.tgz
PROJECT_ID="74648"

LOG_LEVEL?=INFO

##@ Setup

$(TARGET)/.venv-created:
	@echo "🔧 Creating virtualenv..."
	mkdir -p $(TARGET)
	python3 -m venv $(VENV)
	touch $@

$(TARGET)/.uv-installed: $(TARGET)/.venv-created
	@echo "📦 Installing uv..."
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install uv
	touch $@

##@ Dependency Management

.PHONY: dev

dev: $(TARGET)/.compiled ## Install from compiled lock
	@echo "✅ Dependencies installed using uv."

$(TARGET)/.compiled: pyproject.toml $(TARGET)/.uv-installed
	@echo "📄 Compiling lock file and syncing dependencies..."
	$(UV) pip compile --all-extras pyproject.toml --output-file uv.lock
	$(UV) pip sync uv.lock
	touch $@

.PHONY: update

update: $(TARGET)/.uv-installed ## Re-resolve and update all dependencies
	@echo "⬆️  Re-compiling and syncing dependencies..."
	$(UV) pip compile --all-extras pyproject.toml --output-file uv.lock
	$(UV) pip sync uv.lock
	touch $(TARGET)/.compiled

##@ Build

.PHONY: build

build: dev $(TARGET)/.built ## Build current module

$(TARGET)/.built:
	@echo "************ UV BUILD PLACEHOLDER ************"
	touch $@

.PHONY: docker-build

docker-build: ## Build the Docker image
	docker build -t $(IMG) .

.PHONY: helm-package

helm-package: ## Package the Helm chart
	helm package helm-chart/

##@ Image publishing

.PHONY: docker-push

docker-push: ## Push Docker image IMG
	docker push $(IMG)

.PHONY: helm-push

helm-push: ## Push Helm chart to GitLab package registry
	curl --fail-with-body --request POST \
		 --form "chart=@${HELM_ARCHIVE}" \
		 --user ${GITLAB_USER}:${GITLAB_TOKEN} \
		 https://gitlab.thalesdigital.io/api/v4/projects/${PROJECT_ID}/packages/helm/api/release/charts

##@ Run

.PHONY: run

run: dev ## Run the app from source
	PYTHONPATH=. \
	ENV_FILE="$(ENV_FILE)" LOG_LEVEL="$(LOG_LEVEL)" \
	$(PYTHON) ${PY_PACKAGE}/main.py --config-path ./config/configuration.yaml

.PHONY: docker-run

docker-run: ## Run the app in Docker
	docker run -it \
		-p 8111:8111 \
		-v ~/.kube/:/home/fred-user/.kube/ \
		-v ~/.aws/:/home/fred-user/.aws/ \
		-v $(realpath knowledge_flow_app/config/configuration.yaml):/app/configuration.yaml \
		-e LOG_LEVEL="$(LOG_LEVEL)" \
		$(IMG) --config-path /app/configuration.yaml

##@ Tests

.PHONY: test test-app test-processors

test: dev test-processors test-app ## Run all tests

test-app:
	@echo "************ TESTING APP ************"
	$(PYTHON) -m pytest --cov=. --cov-report=html knowledge_flow_app/tests
	@echo "✅ Coverage report: htmlcov/index.html"
	@xdg-open htmlcov/index.html || echo "📎 Open manually htmlcov/index.html"

test-processors:
	@echo "************ TESTING PROCESSORS ************"
	$(PYTHON) -m pytest --cov=. --cov-report=html knowledge_flow_app/input_processors/

##@ Clean

.PHONY: clean clean-package clean-pyc clean-test

clean: clean-package clean-pyc clean-test ## Clean all build/test artifacts
	@echo "🧹 Cleaning project..."
	rm -rf $(VENV)
	rm -rf .cache .mypy_cache

clean-package: ## Clean distribution artifacts
	@echo "************ CLEANING DISTRIBUTION ************"
	rm -rf dist
	rm -rf $(TARGET)

clean-pyc: ## Clean Python bytecode
	@echo "************ CLEANING PYTHON CACHE ************"
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete
	find . -name '*~' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} +

clean-test: ## Clean test cache
	@echo "************ CLEANING TESTS ************"
	rm -rf .tox .coverage htmlcov $(TARGET)/.tested

##@ Help

.PHONY: help

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z0-9._-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
