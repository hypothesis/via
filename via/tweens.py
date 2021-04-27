def robots_tween_factory(handler, _registry):
    def robots_tween(request):
        response = handler(request)

        # If the view hasn't set its own X-Robots-Tag header then set one that
        # tells Google (and most other crawlers) not to index the page and not
        # to follow links on the page.
        #
        # https://developers.google.com/search/reference/robots_meta_tag
        if "X-Robots-Tag" not in response.headers:
            response.headers["X-Robots-Tag"] = "noindex, nofollow"

        return response

    return robots_tween
