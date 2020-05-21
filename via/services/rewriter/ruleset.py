from enum import Enum

import yaml


class RewriteAction(Enum):
    NONE = 0
    """Don't do anything at all"""

    MAKE_ABSOLUTE = 1
    """Convert the URL to be absolute"""

    PROXY_STATIC = 2
    """Proxy the content from us, but leave it unchanged"""

    REWRITE_HTML = 3
    """Rewrite the URL so it will go through our HTML rewriting"""

    REWRITE_CSS = 4
    """Rewrite the URL so it will go through our CSS rewriting"""

    REWRITE_JS = 5
    """Rewrite the URL so it will go through our JS rewriting"""


class Ruleset:
    def __init__(self, ruleset):
        self.ruleset = ruleset

    @classmethod
    def from_yaml(cls, rule_file):
        with open(rule_file) as handle:
            try:
                data = yaml.safe_load(handle)
            except yaml.YAMLError as err:
                raise IOError(f"Could not load ruleset from '{rule_file}'") from err

        return Ruleset(
            tuple(
                (Rule(**rule["match"]), RewriteAction[rule["action"]])
                for rule in data["rules"]
            )
        )

    def action_for(self, tag, attr, url, rel=None):
        ext = self.get_extension(url)

        for rule, action in self.ruleset:
            if rule.applies(tag, attr, ext, rel):
                # print(f"<{tag}:{attr}> {url} -> {action}")
                # if attr and not Attribute.is_interesting(tag, attr):
                #     # This explosion can only be raised by LXML parser, but is
                #     # actually used to improve the HTMLParser object Attribute used
                #     # below. LXML will find things by itself. HTMLParser needs to
                #     # be told what to find
                #     raise ValueError(
                #         f"Missed an interesting attribute: <{tag}:{attr}>: {url}"
                #     )

                return action

        raise RuntimeError(f"No rule caught <{tag}:{attr}> {url}")

    @classmethod
    def get_extension(cls, url):
        if "?" in url:
            url, _ = url.split("?", 1)

        parts = url.rsplit(".", 1)
        if len(parts) == 2:
            return parts[1]

        return None


class Rule:
    WILD = object()

    def __init__(self, tag=WILD, attr=WILD, ext=WILD, rel=WILD):
        self.parts = tuple(
            set(part) if isinstance(part, list) else part
            for part in (tag, attr, ext, rel)
        )

    def applies(self, tag, attribute, extension, rel):
        for our_value, other_value in zip(self.parts, (tag, attribute, extension, rel)):
            if not self._match(our_value, other_value):
                return False

        return True

    def _match(self, our_value, other_value):
        if our_value is self.WILD:
            return True

        if isinstance(our_value, (list, set)):
            return other_value in our_value

        return other_value == our_value

    def __repr__(self):
        parts = []
        for name, value in zip(("tag", "attr", "ext", "rel"), self.parts):
            if value is not self.WILD:
                value = f'"{value}"' if isinstance(value, str) else value
                parts.append(f"{name}={value}")

        return f"{self.__class__.__name__}({', '.join(parts)})"


class Attribute:
    # Style attributes on anything!
    UNIVERSAL = {"style"}

    BY_TAG = {
        "a": {"href", "src"},
        "link": {"href"},
        "img": {"src", "srcset", "data-src"},
        "image": {"src", "srcset", "data-src"},
        "form": {"action"},
        "iframe": {"src"},
        "script": {"src"},
        "blockquote": {"cite"},
        "input": {"src"},
        "head": {"profile"},
    }

    @classmethod
    def is_interesting(self, tag, attr):
        return attr in self.BY_TAG.get(tag, self.UNIVERSAL)
