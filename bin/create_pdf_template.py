"""Create the PDFjs template."""

import importlib_resources

BASE_DIR = importlib_resources.files("via")
SOURCE_FILE = str(BASE_DIR / "static/vendor/pdfjs-2/web/viewer.html")
TARGET_FILE = str(BASE_DIR / "templates/pdf_wrapper.html.jinja2")

# We want control over where these are so we'll remove them
ITEMS_TO_REMOVE = [
    '<link rel="stylesheet" href="viewer.css">',
    '<script src="../build/pdf.js"></script>',
    '<script src="viewer.js"></script>',
]


def _insert(contents, where, pattern, new_content):
    index = contents.index(pattern)

    if where == "after":
        index += len(pattern)

    print(f"Inserting content {where} {pattern} at index: {index}")  # noqa: T201
    before, after = contents[:index], contents[index:]

    return f"{before}{new_content}{after}"


def _insert_jinja2_blocks(contents):
    for where, pattern, block_name in (
        ("after", "</title>", "head"),
        ("before", "</body>", "footer"),
    ):
        contents = _insert(
            contents, where, pattern, f"{{% block {block_name} %}}{{% endblock %}}"
        )

    return contents


if __name__ == "__main__":
    with open(SOURCE_FILE, encoding="utf8") as handle:  # noqa: PTH123
        template = _insert_jinja2_blocks(handle.read())
        template = _insert(
            template,
            "after",
            "<!DOCTYPE html>",
            "\n\n<!--\nTHIS CONTENT IS AUTO GENERATED. DO NOT EDIT!\n"
            "FROM 'bin/create_pdf_template.pdf'\n-->\n",
        )

    for item in ITEMS_TO_REMOVE:
        if item not in template:
            raise ValueError(f"Expected to find '{item}'")  # noqa: EM102, TRY003
        print(f"Removing: {item}")  # noqa: T201
        template = template.replace(item, f"<!-- {item} -->")

    with open(TARGET_FILE, "w", encoding="utf8") as handle:  # noqa: PTH123
        handle.write(template)

    print(f"Created {TARGET_FILE} from {SOURCE_FILE}")  # noqa: T201
