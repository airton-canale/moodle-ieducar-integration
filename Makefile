.PHONY: test run compose-up compose-down relatorio

test:
	pytest

run:
	uvicorn app.main:app --reload --port 8000

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

relatorio:
	cd docs/relatorio && latexmk -pdf relatorio.tex
