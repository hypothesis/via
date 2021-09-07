from h_vialib import Configuration


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

    url = Configuration.strip_from_url(url)

    return url
