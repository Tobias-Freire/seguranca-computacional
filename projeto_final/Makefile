.DEFAULT_GOAL := help
SCENARIO ?= baseline

.PHONY: help up down attack report demo clean test

help: ## Lista os alvos disponíveis
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

up: ## Sobe o laboratório
	@test -f .env || cp .env.example .env
	@mkdir -p data/cowrie/log data/cowrie/downloads
	@chmod 777 data/cowrie/log data/cowrie/downloads  # o Cowrie roda como uid 999
	docker compose up -d --build

down: ## Derruba os containers
	docker compose down

attack: ## Executa um cenário: make attack SCENARIO=baseline (ainda não implementado)
	@echo "ainda não implementado (Parte 5)"

report: ## Gera reports/relatorio.md (ainda não implementado)
	@echo "ainda não implementado (Parte 7)"

demo: ## Roda o roteiro completo da demonstração (ainda não implementado)
	@echo "ainda não implementado (Parte 12)"

clean: ## Remove containers e dados gerados (preserva data/samples)
	docker compose down -v --remove-orphans
	find data/cowrie/log data/cowrie/downloads data/analysis data/hardened -mindepth 1 ! -name .gitkeep -delete

test: ## Roda os testes (ainda não implementado)
	@echo "ainda não implementado (Parte 6)"
