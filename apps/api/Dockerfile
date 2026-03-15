FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY alembic.ini entrypoint.sh ./
COPY alembic/ alembic/
COPY src/ src/

EXPOSE 8000

CMD ["sh", "entrypoint.sh"]
