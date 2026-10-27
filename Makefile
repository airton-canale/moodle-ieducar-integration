.PHONY: test run compose-up compose-down relatorio infra ieducar-install

test:
	pytest

run:
	uvicorn app.main:app --reload --port 8000

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

relatorio:
	cd docs/relatorio && latexmk -pdf -interaction=nonstopmode relatorio.tex

# Versão do i-Educar usada no desenvolvimento da integração
IEDUCAR_REPO := https://github.com/portabilis/i-educar
IEDUCAR_COMMIT := 435649b0474f022db8fe05bb6b0265cf4100258d

infra:
	@if [ ! -d infra/i-educar ]; then \
		git clone $(IEDUCAR_REPO) infra/i-educar && \
		git -C infra/i-educar checkout $(IEDUCAR_COMMIT); \
	else echo "infra/i-educar ja existe"; fi

ieducar-install:
	docker compose exec php composer new-install
	docker compose exec php php artisan db:seed
