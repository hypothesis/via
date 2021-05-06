def url_from_user_input(url):
    """Return a normalized URL from user input.

    Take a URL from user input (eg. a URL input field or path parameter) and
    convert it to a normalized form.
    """
    url = url.strip()
    if not url:
        return url

    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    return url
