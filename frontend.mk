node_modules/.uptodate: package.json yarn.lock
	yarn install
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
