# ============================================================
# ReplyIQ Backend — Makefile
# Run targets with: make <target>
# ============================================================

# Use the virtual environment's Python if it exists
PYTHON = .venv/Scripts/python
PIP = .venv/Scripts/pip

# --- Setup ---
.PHONY: install
install:
	python -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	$(PYTHON) -m pre_commit install
	@echo "Setup complete. Activate with: .venv\Scripts\activate"

# --- Run ---
.PHONY: run
run:
	$(PYTHON) run.py

# --- Testing ---
.PHONY: test
test:
	$(PYTHON) -m pytest tests/ -v --tb=short

.PHONY: coverage
coverage:
	$(PYTHON) -m pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=70

# --- Code Quality ---
.PHONY: lint
lint:
	$(PYTHON) -m flake8 app/ jobs/ tests/

.PHONY: format
format:
	$(PYTHON) -m black app/ jobs/ tests/ run.py
	$(PYTHON) -m isort app/ jobs/ tests/ run.py

.PHONY: check
check: lint test
	@echo "All checks passed."

# --- Cron Jobs (local testing) ---
.PHONY: poller
poller:
	$(PYTHON) jobs/review_poller.py

.PHONY: approval
approval:
	$(PYTHON) jobs/approval_checker.py

# --- Utilities ---
.PHONY: verify-env
verify-env:
	$(PYTHON) scripts/verify_env.py

.PHONY: clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage
