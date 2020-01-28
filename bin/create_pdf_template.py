"""Create the PDFjs template."""

from pkg_resources import resource_filename

SOURCE_FILE = resource_filename("via", "static/vendor/pdfjs-2/web/viewer.html")
TARGET_FILE = resource_filename("via", "templates/pdf_wrapper.html.jinja2")


def _insert(contents, where, pattern, new_content):
    index = contents.index(pattern)

    if where == "after":
        index += len(pattern)

    print(f"Inserting content {where} {pattern} at index: {index}")
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
    # pylint: disable=invalid-name
    # template isn't a global you dolt!

    with open(SOURCE_FILE) as handle:
        template = _insert_jinja2_blocks(handle.read())
        template = _insert(
            template,
            "after",
            "<!DOCTYPE html>",
            "\n\n<!--\nTHIS CONTENT IS AUTO GENERATED. DO NOT EDIT!\n"
            "FROM 'bin/create_pdf_template.pdf'\n-->\n",
        )

    with open(TARGET_FILE, "w") as handle:
        handle.write(template)

    print(f"Created {TARGET_FILE} from {SOURCE_FILE}")
