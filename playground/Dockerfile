# Playground image: the demo app plus greentechhub-ui installed as a wheel
# (non-editable, so the templates and static files ship inside the package,
# as a consumer gets them). Build from the repo root:
#
#     docker build -f playground/Dockerfile -t gth-playground .
#     docker run --rm -p 8500:8500 gth-playground
#
# Published multi-arch (amd64 + arm64) to GHCR by
# .github/workflows/playground-image.yml; see playground/README.md.

ARG PYTHON_IMAGE=python:3.12-slim@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2

FROM ${PYTHON_IMAGE} AS build
# git: the playground extra pins greentechhub-fastapi (and through it
# greentechhub-core) as git+https dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --prefix /install ".[playground]"

FROM ${PYTHON_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=build /install /usr/local
WORKDIR /app
COPY playground ./playground
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin playground
USER 10001
EXPOSE 8500
# Not `python playground/app.py`: its __main__ binds 127.0.0.1 only.
CMD ["uvicorn", "playground.app:app", "--host", "0.0.0.0", "--port", "8500"]
