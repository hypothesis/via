import re

from via.services.rewriter.core import Rewriter


class CSSRewriter(Rewriter):
    URL_REGEX = re.compile(r"url\(([^)]+)\)", re.IGNORECASE)

    def rewrite(self, doc):
        content = doc.content.decode("utf-8")

        replacements = []

        for match in self.URL_REGEX.finditer(content):
            url = match.group(1)

            if url.startswith('"') or url.startswith("'"):
                print("HMMMM QUOTED", url)
                continue

            if url.startswith("/"):
                new_url = self.make_url_absolute(url, doc.url)

                replacements.append((match.group(0), f"url({new_url})"))

        for find, replace in replacements:
            content = content.replace(find, replace)

        return content
