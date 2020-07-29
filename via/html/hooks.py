"""Configuration points which can be added to change `pywb` behavior."""

from urllib.parse import parse_qs, parse_qsl, urlparse

from via.configuration import Configuration


class Hooks:
    # Disable the Content-Security-Policy which blocks our embed
    csp_header = None

    def __init__(self, config):
        self.config = config

    def template_vars(self):
        """Additional parameters to place in the global Jinja2 environment."""
        vars = {"client_params": self.get_client_params}
        vars.update(self.config)
        vars["ignore_prefixes"] = self.ignore_prefixes

        return vars

    @property
    def ignore_prefixes(self):
        """The list of URL prefixes to ignore (server and client side)."""
        return self.config["ignore_prefixes"]

    @classmethod
    def get_client_params(cls, http_env):
        """Return the h-client parameters from a WSGI environment."""

        params = parse_qs(http_env.get("QUERY_STRING"))

        via_params, client_params = Configuration.extract_from_params(params)

        return str(client_params)

    @classmethod
    def filter_doc_url(cls, doc_url):
        """Map a URL before retrieving it for rewriting."""

        parts = urlparse(doc_url)
        query_parts = parse_qsl(parts.query)

        # TODO: Here you would strip out the configuration stuff...
        # return parts._replace(query='wat=bat').geturl()

        # TODO: How does this work when moving from URL to URL via link?

        return doc_url
