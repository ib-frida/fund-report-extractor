FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[dev]"
COPY tests ./tests
COPY config ./config
COPY data/gold ./data/gold
# Default: run the test suite. Override, e.g.: docker run fundx fundx baseline
CMD ["pytest", "-q"]
