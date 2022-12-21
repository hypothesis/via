"""Methods for working with headers."""

from collections import OrderedDict

from h_vialib.secure import SecureSecrets

# A mix of headers we don't want to pass on for one reason or another
BANNED_HEADERS = {
    # Requests needs to set Host to the right thing for us
    "Host",
    # Don't pass Cookies
    "Cookie",
    # AWS things
    "X-Amzn-Trace-Id",
    # AWS NGINX / NGINX things
    "X-Real-Ip",
    "X-Forwarded-Proto",
    "X-Forwarded-Port",
    # Cloudflare things
    "Cf-Request-Id",
    "Cf-Connecting-Ip",
    "Cf-Ipcountry",
    "Cf-Ray",
    "Cf-Visitor",
    "Cdn-Loop",
}

# Something get incorrectly Title-cased by the stack by the time they've got to
# us. If we pass them on like this could mark us out as a bot.
HEADER_MAP = {"Dnt": "DNT"}

# Some values need to be faked or fixed
HEADER_DEFAULTS = {
    # Mimic what it looks like if you got here from a Google search
    "Referer": "https://www.google.com",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    # This gets overwritten by AWS NGINX
    "Connection": "keep-alive",
}


def clean_headers(headers):
    """Remove Cloudflare and other cruft from the headers.

    This will attempt to present a clean version of the headers which can be
    used to make a request to the 3rd party site.

    Also:

      * Map the headers as if we had come from a Google Search
      * Remove things added by AWS and Cloudflare etc.
      * Fix some header names

    This is intended to return a list of headers that can be passed on to the
    upstream service.

    :param headers: A mapping of header values
    :return: An OrderedDict of cleaned headers
    """
    clean = OrderedDict()

    for header_name, value in headers.items():
        if header_name in BANNED_HEADERS:
            continue

        # Map to standard names for things
        header_name = HEADER_MAP.get(header_name, header_name)

        # Add in defaults for certain fields
        value = HEADER_DEFAULTS.get(header_name, value)

        clean[header_name] = value

    return clean


def add_request_headers(headers, request=None):
    """Add headers for 3rd party providers which we access data from."""

    # Pass our abuse policy in request headers for third-party site admins.
    headers["X-Abuse-Policy"] = "https://web.hypothes.is/abuse-policy/"
    headers["X-Complaints-To"] = "https://web.hypothes.is/report-abuse/"

    if request and "via.secret.headers" in request.params:
        # Pass along any headers sent in the original request
        secure_secrets = SecureSecrets(
            request.registry.settings["via_secret"].encode("utf-8")
        )

        secret_headers = secure_secrets.decrypt_dict(
            request.params["via.secret.headers"]
        )
        headers.update(secret_headers)

    return headers
