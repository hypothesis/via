.PHONY: nginx
nginx: python
	@tox -qe dev --run-command 'docker compose run --rm --service-ports nginx-proxy'
