.PHONY: install test db-up db-down pr ship migrate dev


install:
	cd backend && uv sync

test:
	cd backend && uv run pytest tests/ 

db-up:
	docker compose up -d

db-down:
	docker compose down

pr:
ifndef title
	$(error title is required. Usage: make pr title="your title")
endif
	gh pr create --base main --title "$(title)" --body "$(body)"

ship:
ifndef msg
	$(error msg is required. Usage: make ship msg="commit message" title="pr title")
endif
ifndef title
	$(error title is required. Usage: make ship msg="commit message" title="pr title")
endif
	git add -A
	git commit -m "$(msg)"
	git push -u origin HEAD
	gh pr create --base main --title "$(title)" --body "$(body)"

migrate:
ifndef msg
	$(error msg is required. Usage: make migrate msg="alembic migration message")
endif
	cd backend && uv run alembic revision --autogenerate -m "$(msg)" && uv run alembic upgrade head

dev:
	docker compose up -d
	sleep 1
	cd backend && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
