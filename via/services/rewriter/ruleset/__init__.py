from functools import lru_cache

from pkg_resources import resource_filename

from via.services.rewriter.ruleset.ruleset import Attribute, RewriteAction, Ruleset


class Rules:
    """Lazy caching loader for rules."""

    @classmethod
    def js(cls):
        return cls.html()

    @classmethod
    def css(cls):
        return cls._load("css.yaml")

    @classmethod
    def html(cls):
        return cls._load("html.yaml")

    @classmethod
    @lru_cache(4)
    def _load(cls, filename):
        return Ruleset.from_yaml(
            resource_filename("via.services.rewriter.ruleset", filename)
        )
