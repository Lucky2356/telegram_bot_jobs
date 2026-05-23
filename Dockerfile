# Stage 1: Build frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/web/frontend
COPY web/frontend/package.json web/frontend/package-lock.json ./
RUN npm ci
COPY web/frontend/ .
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ core/
COPY scrapers/ scrapers/
COPY bot/ bot/
COPY web/ web/
COPY main.py .
COPY alembic.ini .
COPY alembic/ alembic/

COPY --from=frontend-builder /app/web/frontend/dist /app/web/frontend/dist

VOLUME ["/app/data"]
ENV DATABASE_URL=sqlite+aiosqlite:///./data/vacancies.db

EXPOSE 8000

CMD ["python", "main.py"]
