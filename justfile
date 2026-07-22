# Install dependencies
install:
    poetry install

# Run the application
run:
    poetry run python app.py

# Run tests
test:
    poetry run pytest

# Run linting
lint:
    poetry run ruff check .

# Format code
fmt:
    poetry run ruff format .
