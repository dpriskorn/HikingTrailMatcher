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

# Generate osmChange file for JOSM upload
osmchange:
    poetry run python app_osmchange.py
