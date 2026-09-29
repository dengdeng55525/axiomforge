# Optional application container only: does not download or serve an LLM.
FROM node:22-bookworm-slim AS web-build
WORKDIR /frontend
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-fund
COPY web ./
RUN npm run build

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
COPY --from=web-build /frontend/dist ./web/dist
COPY schemas ./schemas
RUN pip install --no-deps . && useradd --create-home --uid 10001 algoforge && mkdir -p /app/artifacts /app/data/raw && chown -R algoforge:algoforge /app
USER algoforge
ENV ALGOFORGE_ROOT=/app
CMD ["algoforge", "serve", "--host", "0.0.0.0", "--port", "8000"]
