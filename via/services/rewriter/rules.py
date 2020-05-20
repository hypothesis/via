from enum import Enum


class RewriteAction(Enum):
    NONE = 0
    MAKE_ABSOLUTE = 1
    PROXY_STATIC = 2
    REWRITE_HTML = 3
    REWRITE_CSS = 4


class Rule:
    WILD = object()

    def __init__(self, tag=WILD, attrs=WILD, ext=WILD, rel=WILD):
        self.tag = tag
        self.attribute = attrs
        self.extensions = ext

        self.parts = (tag, attrs, ext, rel)

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


class RewriteRules:
    # High level configurable behaviors
    ACTION_HTML_LINKS = RewriteAction.REWRITE_HTML
    ACTION_EXTERNAL_CSS = RewriteAction.REWRITE_CSS
    ACTION_EXTERNAL_JS = RewriteAction.PROXY_STATIC

    ACTION_FONT = RewriteAction.PROXY_STATIC
    ACTION_IMAGES = RewriteAction.MAKE_ABSOLUTE
    ACTION_FORMS = RewriteAction.MAKE_ABSOLUTE

    # Extensions
    EXT_IMAGE = {"png", "jpg", "jpeg", "gif", "svg"}
    EXT_FONT = {"woff", "woff2", "ttf", "eot"}

    RULESET = (
        (Rule("form"), ACTION_FORMS),
        (Rule(ext=EXT_FONT), ACTION_FONT),
        # Javascript rules
        (Rule("script", "src"), ACTION_EXTERNAL_JS),
        (Rule(ext="js"), ACTION_EXTERNAL_JS),
        # Image rules
        (Rule(ext=EXT_IMAGE), ACTION_IMAGES),
        (Rule("img", {"src", "srcset", "data-src"}), ACTION_IMAGES),
        (Rule("input", "src"), ACTION_IMAGES),
        # Links
        (Rule("a", "href"), ACTION_HTML_LINKS),
        (Rule("link", rel="stylesheet"), ACTION_EXTERNAL_CSS),
        (Rule("link", "href", "css"), ACTION_EXTERNAL_CSS),
        # Default
        (Rule(), RewriteAction.MAKE_ABSOLUTE),
    )

    @classmethod
    def action_for(cls, tag, attr, url, rel=None):
        ext = cls.get_extension(url)

        for rule, action in cls.RULESET:
            if rule.applies(tag, attr, ext, rel):
                # print(f"<{tag}:{attr}> {url} -> {action}")
                if attr and not Attribute.is_interesting(tag, attr):
                    # This exploision can only be raised by LXML parser, but is
                    # actually used to improve the HTMLParser object Attribute used
                    # below. LXML will find things by itself. HTMLParser needs to
                    # be told what to find
                    raise ValueError(
                        f"Missed an interesting attribute: <{tag}:{attr}>: {url}"
                    )

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


class Attribute:
    UNIVERSAL = {"style"}
    BY_TAG = {
        "a": {"href", "src"},
        "link": {"href"},
        "img": {"src", "srcset", "data-src"},
        "form": {"action"},
        "iframe": {"src"},
        "script": {"src"},
        "blockquote": {"cite"},
        "input": {"src"}
        # Style attributes on anything!
    }

    @classmethod
    def is_interesting(self, tag, attr):
        return attr in self.BY_TAG.get(tag, self.UNIVERSAL)
