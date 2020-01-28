.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo "make dev               Run the app in the development server"
	@echo 'make services          Run the services that `make dev` requires'
	@echo 'make build            Prepare the build files'
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run the unit tests"
	@echo "make coverage          Print the unit test coverage report"
	@echo "make docstrings        View all the docstrings locally as HTML"
	@echo "make checkdocstrings   Crash if building the docstrings fails"
	@echo "make update-pdfjs      Update our copy of PDF-js"
	@echo "make pip-compile       Compile requirements.in to requirements.txt"
	@echo "make upgrade-package   Upgrade the version of a package in requirements.txt."
	@echo '                       Usage: `make upgrade-package name=some-package`.'
	@echo "make docker            Make the app's Docker image"
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: dev
dev: python
	@tox -qe dev

.PHONY: build
build: python
	@tox -qe build

.PHONY: services
services: args?=up -d
services: python
	@tox -qe docker-compose -- $(args)

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

.PHONY: update-pdfjs
update-pdfjs: python
	@tox -qe update-pdfjs

.PHONY: coverage
coverage: python
	@tox -qe coverage

.PHONY: docstrings
docstrings: python
	@tox -qe docstrings

.PHONY: checkdocstrings
checkdocstrings: python
	@tox -qe checkdocstrings

.PHONY: pip-compile
pip-compile: python
	@tox -qe pip-compile

.PHONY: upgrade-package
upgrade-package: python
	@tox -qe pip-compile -- --upgrade-package $(name)

.PHONY: docker
docker: build
	@git archive --format=tar HEAD > build.tar
	@tar --update -f build.tar py_proxy/static
	@gzip -c build.tar | docker build -t hypothesis/py_proxy:$(DOCKER_TAG) -
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
