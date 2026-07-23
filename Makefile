SHELL := /bin/bash

PYTHON ?= python3
VENV_PYTHON := .venv/bin/python
BACKEND_INSTALL_STAMP := .venv/.lain5g-dev-deps

.PHONY: version-check images-check images-pull build-5g-sa start-5g-sa stop-5g-sa restart-5g-sa status-5g-sa logs-5g-sa validate-5g-sa clean-5g-sa backend-install backend-dev backend-test backend-cov frontend-install frontend-dev frontend-build frontend-test app-build app-up app-down app-logs app-ps subscribers-test subscribers-integration-test build-4g-lte-sim start-4g-lte-sim stop-4g-lte-sim restart-4g-lte-sim status-4g-lte-sim logs-4g-lte-sim validate-4g-lte-sim test-4g-lte-sim build-4g-volte-sim start-4g-volte-sim stop-4g-volte-sim status-4g-volte-sim logs-4g-volte-sim validate-4g-volte-sim test-4g-volte-sim build-4g-lte-x310 check-x310 preflight-4g-lte-x310 start-4g-lte-x310-epc start-4g-lte-x310-rf emergency-stop-4g-lte-x310 stop-4g-lte-x310 status-4g-lte-x310 logs-4g-lte-x310 validate-4g-lte-x310 test-4g-lte-x310 build-5g-vonr-sim start-5g-vonr-sim stop-5g-vonr-sim restart-5g-vonr-sim status-5g-vonr-sim logs-5g-vonr-sim validate-5g-vonr-sim test-5g-vonr-sim build-5g-x310 check-5g-x310 preflight-5g-x310 start-5g-x310-core dry-run-5g-x310 start-5g-x310-rf emergency-stop-5g-x310 stop-5g-x310 status-5g-x310 logs-5g-x310 test-5g-x310
.PHONY: test verify softwarex-check frontend-typecheck source-formats-check compose-check profile-check links-check release-artifacts-check public-results-check secret-scan

version-check:
	@python3 scripts/release/check-version.py

images-check:
	@./lain5g images list all

images-pull:
	@./lain5g images pull all

build-5g-sa:
	@if [ "$${LAIN5G_DRY_RUN:-false}" = "true" ]; then \
		echo "docker build -t lain5g-lab/open5gs:local images/open5gs"; \
		echo "docker build -t lain5g-lab/ueransim:local images/ueransim"; \
	else \
		docker build -t lain5g-lab/open5gs:local images/open5gs && \
		docker build -t lain5g-lab/ueransim:local images/ueransim; \
	fi

start-5g-sa:
	@deployments/5g-sa/scripts/start.sh

stop-5g-sa:
	@deployments/5g-sa/scripts/stop.sh

restart-5g-sa:
	@deployments/5g-sa/scripts/restart.sh

status-5g-sa:
	@deployments/5g-sa/scripts/status.sh

logs-5g-sa:
	@deployments/5g-sa/scripts/logs.sh

validate-5g-sa:
	@deployments/5g-sa/scripts/validate.sh

clean-5g-sa:
	@if [ "$${LAIN5G_DRY_RUN:-false}" = "true" ]; then \
		echo "docker compose --env-file deployments/5g-sa/.env -f deployments/5g-sa/docker-compose.yml down -v --remove-orphans"; \
	else \
		docker compose --env-file deployments/5g-sa/.env -f deployments/5g-sa/docker-compose.yml down -v --remove-orphans; \
	fi

backend-install: $(BACKEND_INSTALL_STAMP)

$(BACKEND_INSTALL_STAMP): backend/constraints.txt backend/requirements.txt backend/requirements-dev.txt
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install --upgrade pip==25.1.1
	$(VENV_PYTHON) -m pip install --constraint backend/constraints.txt --requirement backend/requirements.txt --requirement backend/requirements-dev.txt
	@touch $@

backend-dev:
	.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

backend-test: backend-install
	$(VENV_PYTHON) -m pytest backend/tests

backend-cov: backend-install
	$(VENV_PYTHON) -m pytest --cov=backend/app --cov-report=term-missing backend/tests

frontend-install:
	cd frontend && npm ci

frontend-dev:
	cd frontend && npm run dev

frontend-build: frontend-install
	cd frontend && npm run build

frontend-test: frontend-install
	cd frontend && npm test

frontend-typecheck: frontend-install
	cd frontend && ./node_modules/.bin/tsc -b --pretty false

source-formats-check: backend-install
	$(VENV_PYTHON) scripts/verify/source_formats.py

compose-check: backend-install
	$(VENV_PYTHON) scripts/verify/compose.py

profile-check: backend-install
	$(VENV_PYTHON) scripts/verify/profiles.py

links-check: backend-install
	$(VENV_PYTHON) scripts/verify/internal_links.py

release-artifacts-check: backend-install
	$(VENV_PYTHON) scripts/verify/release_artifacts.py

public-results-check:
	$(PYTHON) scripts/verify/public_results.py

secret-scan:
	@./scripts/security/check-sensitive-files.sh

test: backend-cov frontend-test frontend-typecheck frontend-build
	@printf '%s\n' 'test: OK'

verify: source-formats-check compose-check profile-check version-check links-check secret-scan release-artifacts-check public-results-check
	@printf '%s\n' 'verify: OK'

softwarex-check: test verify
	@printf '%s\n' 'softwarex-check: OK'

app-build:
	@if [ ! -f .env.app ]; then \
		echo "Missing .env.app. Create it with: cp .env.app.example .env.app" >&2; \
		exit 2; \
	fi
	docker compose --env-file .env.app -f docker-compose.app.yml build

app-up:
	@if [ ! -f .env.app ]; then \
		echo "Missing .env.app. Create it with: cp .env.app.example .env.app" >&2; \
		exit 2; \
	fi
	docker compose --env-file .env.app -f docker-compose.app.yml up -d --build

app-down:
	@if [ ! -f .env.app ]; then \
		echo "Missing .env.app. Create it with: cp .env.app.example .env.app" >&2; \
		exit 2; \
	fi
	docker compose --env-file .env.app -f docker-compose.app.yml down

app-logs:
	@if [ ! -f .env.app ]; then \
		echo "Missing .env.app. Create it with: cp .env.app.example .env.app" >&2; \
		exit 2; \
	fi
	docker compose --env-file .env.app -f docker-compose.app.yml logs -f

app-ps:
	@if [ ! -f .env.app ]; then \
		echo "Missing .env.app. Create it with: cp .env.app.example .env.app" >&2; \
		exit 2; \
	fi
	docker compose --env-file .env.app -f docker-compose.app.yml ps

subscribers-test:
	.venv/bin/pytest backend/tests/test_open5gs_connection_service.py backend/tests/test_subscriber_service.py backend/tests/test_subscribers_api.py
	cd frontend && npm test -- subscribers

subscribers-integration-test:
	@if [ "$${LAIN5G_ALLOW_INTEGRATION_WRITES:-false}" != "true" ]; then \
		echo "Refusing to modify Open5GS MongoDB. Set LAIN5G_ALLOW_INTEGRATION_WRITES=true to run subscriber integration writes." >&2; \
		exit 2; \
	fi
	@echo "Run the documented subscriber integration workflow in docs/subscribers.md."

build-4g-lte-sim:
	docker build -t lain5g-lab/open5gs:local images/open5gs
	docker build -t lain5g-lab/srsran4g-sim:local images/srsran4g-sim

start-4g-lte-sim:
	@deployments/4g-lte-sim/scripts/start.sh

stop-4g-lte-sim:
	@deployments/4g-lte-sim/scripts/stop.sh

restart-4g-lte-sim:
	@deployments/4g-lte-sim/scripts/restart.sh

status-4g-lte-sim:
	@deployments/4g-lte-sim/scripts/status.sh

logs-4g-lte-sim:
	@deployments/4g-lte-sim/scripts/logs.sh

validate-4g-lte-sim:
	@deployments/4g-lte-sim/scripts/validate.sh

test-4g-lte-sim:
	.venv/bin/pytest backend/tests/test_4g_lte_sim_static.py
	@deployments/4g-lte-sim/scripts/test.sh

build-4g-volte-sim:
	docker build -t lain5g-lab/srsran4g-sim:local images/srsran4g-sim
	docker build -t lain5g-lab/kamailio:local images/kamailio
	docker build -t lain5g-lab/ims-dns:local images/ims-dns
	docker build -t lain5g-lab/ims-sip:local images/ims-sip

start-4g-volte-sim:
	@deployments/4g-volte/sim/scripts/start.sh

stop-4g-volte-sim:
	@deployments/4g-volte/sim/scripts/stop.sh

status-4g-volte-sim:
	@deployments/4g-volte/sim/scripts/status.sh

logs-4g-volte-sim:
	@deployments/4g-volte/sim/scripts/logs.sh

validate-4g-volte-sim:
	@deployments/4g-volte/sim/scripts/validate.sh

test-4g-volte-sim:
	.venv/bin/pytest backend/tests/test_4g_volte_static.py
	@deployments/4g-volte/sim/scripts/test.sh

build-4g-lte-x310:
	docker build -t lain5g-lab/srsran4g-uhd:local images/srsran4g-uhd
	docker build -t lain5g-lab/kamailio:local images/kamailio
	docker build -t lain5g-lab/ims-dns:local images/ims-dns

check-x310:
	@deployments/4g-volte/x310/scripts/hardware-check.sh
	@deployments/4g-volte/x310/scripts/uhd-check.sh
	@deployments/4g-volte/x310/scripts/fpga-check.sh

preflight-4g-lte-x310:
	@deployments/4g-volte/x310/scripts/preflight.sh

start-4g-lte-x310-epc:
	@deployments/4g-volte/x310/scripts/start-epc.sh

start-4g-lte-x310-rf:
	@deployments/4g-volte/x310/scripts/start-enb.sh

emergency-stop-4g-lte-x310:
	@deployments/4g-volte/x310/scripts/emergency-stop.sh

stop-4g-lte-x310:
	@deployments/4g-volte/x310/scripts/stop.sh

status-4g-lte-x310:
	@deployments/4g-volte/x310/scripts/status.sh

logs-4g-lte-x310:
	@deployments/4g-volte/x310/scripts/logs.sh

validate-4g-lte-x310:
	@deployments/4g-volte/x310/scripts/validate.sh

test-4g-lte-x310:
	.venv/bin/pytest backend/tests/test_4g_volte_static.py
	@deployments/4g-volte/x310/scripts/test.sh

build-5g-vonr-sim:
	docker build -t lain5g-lab/open5gs:local images/open5gs
	docker build -t lain5g-lab/ueransim:local images/ueransim
	docker build -t lain5g-lab/kamailio:local images/kamailio
	docker build -t lain5g-lab/ims-dns:local images/ims-dns
	docker build -t lain5g-lab/ims-sip:local images/ims-sip

start-5g-vonr-sim:
	@deployments/5g-vonr/scripts/start.sh

stop-5g-vonr-sim:
	@deployments/5g-vonr/scripts/stop.sh

restart-5g-vonr-sim:
	@deployments/5g-vonr/scripts/restart.sh

status-5g-vonr-sim:
	@deployments/5g-vonr/scripts/status.sh

logs-5g-vonr-sim:
	@deployments/5g-vonr/scripts/logs.sh

validate-5g-vonr-sim:
	@deployments/5g-vonr/scripts/validate.sh

test-5g-vonr-sim:
	.venv/bin/pytest backend/tests/test_5g_vonr_static.py
	@deployments/5g-vonr/scripts/test.sh

build-5g-x310:
	docker build -t lain5g-lab/srsranproject-uhd:local images/srsranproject-uhd

check-5g-x310:
	@deployments/5g-sa-x310/scripts/hardware-check.sh

preflight-5g-x310:
	@deployments/5g-sa-x310/scripts/preflight.sh

start-5g-x310-core:
	@deployments/5g-sa-x310/scripts/start-core.sh

dry-run-5g-x310:
	@LAIN5G_DRY_RUN=true deployments/5g-sa-x310/scripts/start-gnb.sh

start-5g-x310-rf:
	@deployments/5g-sa-x310/scripts/start-gnb.sh

emergency-stop-5g-x310:
	@deployments/5g-sa-x310/scripts/emergency-stop.sh

stop-5g-x310:
	@deployments/5g-sa-x310/scripts/stop.sh

status-5g-x310:
	@deployments/5g-sa-x310/scripts/status.sh

logs-5g-x310:
	@deployments/5g-sa-x310/scripts/logs.sh

test-5g-x310:
	.venv/bin/pytest backend/tests/test_5g_x310_static.py
	@deployments/5g-sa-x310/scripts/test.sh

IMS_REAL_FLAGS ?=

.PHONY: ims-real-images ims-real-preflight ims-real-status ims-real-stop

ims-real-images:
	.venv/bin/python scripts/ims_real.py images $(IMS_REAL_FLAGS)

ims-real-preflight:
	.venv/bin/python scripts/ims_real.py preflight $(IMS_REAL_FLAGS)

ims-real-status:
	.venv/bin/python scripts/ims_real.py status $(IMS_REAL_FLAGS)

ims-real-stop:
	.venv/bin/python scripts/ims_real.py stop $(IMS_REAL_FLAGS)
