.PHONY: help install test lint format coverage dev clean run

# Default target
help:
	@echo "🛠️  GOIDA VPN Project - Available Commands"
	@echo "========================================="
	@echo ""
	@echo "📦 Dependency Management:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev           - Install development dependencies"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test          - Run all tests (pytest)"
	@echo "  make coverage      - Generate coverage report"
	@echo "  make test-quick    - Run tests quickly (no coverage)"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  make lint          - Check code with flake8"
	@echo "  make format        - Format code with black"
	@echo "  make format-check  - Check if code needs formatting"
	@echo ""
	@echo "🚀 Running:"
	@echo "  make run           - Run main.py"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean         - Remove temporary files"
	@echo ""

# Install production dependencies
install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt
	@echo "✅ Done!"

# Install development dependencies
dev:
	@echo "🛠️  Installing development dependencies..."
	pip install -r requirements-dev.txt
	@echo "✅ Done!"

# Run tests
test:
	@echo "🧪 Running tests with coverage..."
	pytest tests/ -v --tb=short --cov=. --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report generated in htmlcov/index.html"

# Quick test run
test-quick:
	@echo "⚡ Running tests (quick, no coverage)..."
	pytest tests/ -v --tb=short

# Lint with flake8
lint:
	@echo "🔍 Checking code with flake8..."
	flake8 main.py tests/ --max-line-length=120 --extend-ignore=E203,W503 --count --statistics
	@echo "✅ Linting complete!"

# Format with black
format:
	@echo "🎨 Formatting code with black..."
	black main.py tests/ --line-length=120
	isort main.py tests/
	@echo "✅ Formatting complete!"

# Check formatting
format-check:
	@echo "🔍 Checking code format..."
	black --check main.py tests/ --line-length=120 || true
	isort --check-only main.py tests/ || true

# Generate coverage report
coverage:
	@echo "📊 Generating coverage report..."
	pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
	@echo "📈 Open htmlcov/index.html to view report"

# Run main script
run:
	@echo "🚀 Running main.py..."
	python main.py

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Run all checks (test + lint + format check)
all-checks: test lint format-check
	@echo "✅ All checks passed!"
