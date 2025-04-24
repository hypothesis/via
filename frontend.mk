node_modules/.uptodate: package.json yarn.lock
	yarn install
	yarn playwright install chromium
	@touch $@

dev: node_modules/.uptodate

.PHONY: build
$(call help,make build,"prepare the build files")
build: python node_modules/.uptodate
	@tox -qe build

.PHONY: update-pdfjs
$(call help,make update-pdfjs,"update our copy of PDF.js")
update-pdfjs: python
	@tox -qe updatepdfjs

.PHONY: frontend-lint
$(call help,make frontend-lint,"lint the frontend code")
frontend-lint: node_modules/.uptodate
	@yarn checkformatting
	@yarn lint
	@yarn typecheck

.PHONY: frontend-format
$(call help,make frontend-format,"format the frontend code")
frontend-format: node_modules/.uptodate
	@yarn format

.PHONY: frontend-test
$(call help,make frontend-test,"run the frontend tests")
frontend-test: node_modules/.uptodate
	@yarn test $(ARGS)
