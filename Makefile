.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo "make dev               Run the app in the development server"
	@echo "make supervisor        Launch a supervisorctl shell for managing the processes "
	@echo '                       that `make dev` starts, type `help` for docs'
	@echo "make shell             Launch a Python shell in the dev environment"
	@echo 'make services          Run the services that `make dev` requires'
	@echo 'make build             Prepare the build files'
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run the unit tests and produce a coverage report"
	@echo "make sure              Make sure that the formatter, linter, tests, etc all pass"
	@echo "make update-pdfjs      Update our copy of PDF-js"
	@echo "make docker            Make the app's Docker image"
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"
	@echo "make requirements      Compile all requirements files"

.PHONY: dev
dev: python
	@tox -qe dev

.PHONY: supervisor
supervisor: python
	@tox -qe dev --run-command 'supervisorctl -c conf/supervisord-dev.conf $(command)'

.PHONY: devdata
devdata: python
	@tox -qe dev -- python bin/devdata.py

.PHONY: shell
shell: python
	@tox -qe dev --run-command 'pshell conf/development.ini'

.PHONY: build
build: python
	@tox -qe build

.PHONY: services
services:
	@true

.PHONY: lint
lint: python
	@tox -qe lint

.PHONY: format
format: python
	@tox -qe format

.PHONY: checkformatting
checkformatting: python
	@tox -qe checkformatting

.PHONY: test
test: python
	@tox -q

.PHONY: sure
sure: checkformatting lint test

.PHONY: update-pdfjs
update-pdfjs: python
	@tox -qe updatepdfjs

.PHONY: docker
docker: build
	@git archive --format=tar HEAD > build.tar
	@tar --update -f build.tar via/static
	@gzip -c build.tar | docker build -t hypothesis/via3:$(DOCKER_TAG) -
	@rm build.tar

.PHONY: clean
clean:
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type f -name "*.gz" -delete

.PHONY: web
web: python
	@tox -qe dev --run-command 'gunicorn -c conf/gunicorn/dev.conf.py --paste conf/development.ini'

.PHONY: nginx
nginx: python
	@tox -qe dev --run-command 'docker-compose run --rm --service-ports nginx-proxy'

.PHONY: rewriter
rewriter:
	@tox -qe dev --run-command 'uwsgi via/rewriter/conf/development.ini'

.PHONY: python
python:
	@./bin/install-python

.PHONY: requirements
requirements:
	@requirements/compile.sh

DOCKER_TAG = dev
