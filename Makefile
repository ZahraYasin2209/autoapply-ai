.PHONY: install run migrate migration downgrade db up down build test shell mcp

install:
	pip install -r config/requirements/dev.txt

run:
	uvicorn autoapply.main:app --reload --host 0.0.0.0 --port 8000

db:
	docker-compose up db -d

up:
	docker-compose up db -d && alembic upgrade head && uvicorn autoapply.main:app --reload --host 0.0.0.0 --port 8000

down:
	docker-compose down

build:
	docker-compose up --build

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(msg)"

downgrade:
	alembic downgrade -1

test:
	pytest tests/ -v

shell:
	python -c "from autoapply.database import SessionLocal; db = SessionLocal(); print('DB connected')"

mcp:
	python autoapply/ai/mcp_server/mcp_server.py
