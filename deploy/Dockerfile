# Optional application container only: does not download or serve an LLM.
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt pyproject.toml README.md ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY configs ./configs
COPY knowledge ./knowledge
COPY docs ./docs
COPY scripts ./scripts
COPY examples ./examples
COPY ui ./ui
COPY schemas ./schemas
RUN pip install --no-deps . && useradd --create-home --uid 10001 algoforge && mkdir -p /app/artifacts /app/data/raw && chown -R algoforge:algoforge /app
USER algoforge
ENV ALGOFORGE_ROOT=/app
CMD ["algoforge", "serve", "--host", "0.0.0.0", "--port", "8000"]
