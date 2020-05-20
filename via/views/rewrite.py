from pyramid import view

from via.services.document import Document
from via.services.rewriter import RewriterService
from via.services.timeit import timeit


@view.view_config(
    route_name="view_css", http_cache=0,
)
def view_css(context, request):
    return _rewrite(
        context,
        request,
        expect_type="text/css",
        rewrite_provider=RewriterService(context, request).get_css_rewriter,
        timeout=3,
    )


@view.view_config(
    route_name="view_js", http_cache=0,
)
def view_js(context, request):
    return _rewrite(
        context,
        request,
        expect_type="javascript",
        rewrite_provider=RewriterService(context, request).get_js_rewriter,
        timeout=3,
    )


@view.view_config(
    route_name="view_html", http_cache=0,
)
def view_html(context, request):
    return _rewrite(
        context,
        request,
        expect_type="text/html",
        rewrite_provider=RewriterService(context, request).get_html_rewriter,
    )


def _rewrite(context, request, expect_type, rewrite_provider, timeout=10):
    document_url = context.url()

    doc = Document(document_url)
    doc.get_original(headers=request.headers, expect_type=expect_type, timeout=timeout)

    rewriter = rewrite_provider(doc.url)

    with timeit(f"{expect_type} rewriting total"):
        doc.content = rewriter.rewrite(doc)

    return doc.response()
