.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo "make dev               Run the app in the development server"
	@echo 'make services          Run the services that `make dev` requires'
	@echo 'make build             Prepare the build files'
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run the unit tests and produce a coverage report"
	@echo "make sure              Make sure that the formatter, linter, tests, etc all pass"
	@echo "make update-pdfjs      Update our copy of PDF-js"
	@echo "make pip-compile       Compile requirements.in to requirements.txt"
	@echo "make upgrade-package   Upgrade the version of a package in requirements.txt."
	@echo '                       Usage: `make upgrade-package name=some-package`.'
	@echo "make docker            Make the app's Docker image"
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: dev
dev: python
	@tox -qe dev -- honcho start

.PHONY: devdata
devdata: python
	@tox -qe dev -- python bin/devdata.py

.PHONY: web
web: python
	@tox -qe dev

.PHONY: nginx
nginx: args?=up
nginx: python
	@tox -qe docker-compose -- $(args)

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
	@tox -qe update-pdfjs

.PHONY: pip-compile
pip-compile: python
	@tox -qe pip-compile

.PHONY: upgrade-package
upgrade-package: python
	@tox -qe pip-compile -- --upgrade-package $(name)

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

.PHONY: python
python:
	@./bin/install-python

DOCKER_TAG = dev
