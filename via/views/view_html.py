from pyramid import view

from via.services.document import Document
from via.services.rewriter import RewriterService
from via.services.timeit import timeit


@view.view_config(
    route_name="view_css", http_cache=3600,
)
def view_css(context, request):
    document_url = context.url()

    doc = Document(document_url)
    doc.get_original(headers=request.headers, expect_type="text/css", timeout=3)

    css_rewriter = RewriterService(context, request).get_css_rewriter(doc.url)

    with timeit("rewriting total"):
        doc.content = css_rewriter.rewrite(doc)

    return doc.response()


@view.view_config(
    route_name="view_html", http_cache=0,
)
def view_html(context, request):
    document_url = context.url()

    doc = Document(document_url)
    doc.get_original(headers=request.headers, expect_type="text/html")

    html_rewriter = RewriterService(context, request).get_html_rewriter(doc.url)

    with timeit("rewriting total"):
        doc.content = html_rewriter.rewrite(doc)

    return doc.response()
