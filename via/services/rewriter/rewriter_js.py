import re

from via.services.rewriter.rewriter import AbstractRewriter


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

            if new_url != url:
                print("REPLACE!", url, ">>", new_url)
                # replacements.append((match.group(0), f"url({quotes}{new_url}{quotes})"))

        for find, replace in replacements:
            content = content.replace(find, replace)

        return content
