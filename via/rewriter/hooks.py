"""Configuration points which can be added to change `pywb` behavior."""

from h_vialib import Configuration


class Hooks:
    """A collection of configuration points for `pywb`."""

    # Disable the Content-Security-Policy which blocks our embed
    csp_header = None

    def __init__(self, config):
        self.config = config

    @property
    def template_vars(self):
        """Get variables to make available in the global Jinja2 environment."""

        template_vars = {"client_params": lambda http_env: self.get_config(http_env)[1]}
        template_vars.update(self.config)

        # This is already in the config, but run through the property just in
        # case that grows some logic in it
        template_vars["ignore_prefixes"] = self.ignore_prefixes

        return template_vars

    @property
    def ignore_prefixes(self):
        """Get the list of URL prefixes to ignore (server and client side)."""

        return self.config["ignore_prefixes"]

    @classmethod
    def get_config(cls, http_env):
        """Return the h-client parameters from a WSGI environment."""

        return Configuration.extract_from_wsgi_environment(http_env)

    @classmethod
    def get_upstream_url(cls, doc_url):
        """Modify the URL before we attempt to get it from ourselves."""

        # The major reason to do this is to ensure the "canonical" URL in the
        # page is correct. Most other URLs are resources in the page which
        # don't have any of our params anyway
        return Configuration.strip_from_url(doc_url)
