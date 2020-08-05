import re

from via.services.rewriter.interface import AbstractRewriter


def _get_exported_vars(js_source):
    # Perform a crude scan of JS source text to extract potential names of
    # top-level `var` identifiers. To reduce the number of non-top level variables
    # matched, we apply a length restriction. This filters out most inner variables
    # due to their names being shortened after minification.
    JS_VAR_REGEX = re.compile(r"var ([a-zA-Z0-9_$]{3,})")
    return JS_VAR_REGEX.findall(js_source)


class JSRewriter(AbstractRewriter):
    QUOTED_URL_REGEX = re.compile(r"[\"'](https?://[^\"']+)[\"']", re.IGNORECASE)

    def rewrite(self, doc):
        content = doc.content.decode("utf-8")

        replacements = []

        for match in self.QUOTED_URL_REGEX.finditer(content):
            url = match.group(1)
            print("JS FIND!", url)

            quotes = ""

            if url.startswith('"') or url.startswith("'"):
                quotes = url[0]
                url = url.strip("\"'")

            new_url = self.url_rewriter.rewrite(
                tag="external-js", attribute=None, url=url
            )
            if not new_url:
                continue

            if new_url != url:
                print("REPLACE!", url, ">>", new_url)
                # replacements.append((match.group(0), f"url({quotes}{new_url}{quotes})"))

        for find, replace in replacements:
            content = content.replace(find, replace)

        # Wrap script content in an IIFE so we can intercept accesses to `location`
        # and other _unforgeable_ properties which can't be monkey-patched directly by
        # client-side JS. See https://html.spec.whatwg.org/ for a complete
        # list of "LegacyUnforgeable" properties.
        #
        # An issue with this is that any variables declared at the top level are no longer
        # visible to other scripts but instead become scoped to the IIFE function.
        # To work around that, we perform a crude scan of the source text to find
        # possible exported variable names and then re-export them.
        exported_vars = _get_exported_vars(content)
        content = (
            """
var exportedVars = {};
(function (window, location) {
"""
            + content
            + ";"
            + ";".join(
                [
                    f"exportedVars['{name}']=typeof {name} !== 'undefined' ? {name} : undefined"
                    for name in exported_vars
                ]
            )
            + """
}).call(viaWindowProxy, viaWindowProxy, viaWindowProxy.location);
"""
            + "".join(
                [
                    f"var {name}; if (exportedVars['{name}']) {{ {name} = exportedVars['{name}'] }}"
                    for name in exported_vars
                ]
            )
        )

        return content
