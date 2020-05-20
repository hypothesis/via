from pyramid import view

from via.configuration import Configuration
from via.services.document import Document
from via.services.rewriter import CSSRewriter, LXMLRewriter
from via.services.timeit import timeit


@view.view_config(
    route_name="view_css", http_cache=3600,
)
def view_css(context, request):
    document_url = context.url()

    doc = Document(document_url)
    doc.get_original(headers=request.headers, expect_type="text/css")

    rewriter = CSSRewriter(
        static_url=context.static_proxy_url_for(""), route_url=request.route_url
    )

    with timeit("rewriting total"):
        doc.content = rewriter.rewrite(doc)

    return doc.response()


@view.view_config(
    route_name="view_html", http_cache=3600,
)
def view_pdf(context, request):
    document_url = context.url()

    doc = Document(document_url)
    doc.get_original(headers=request.headers, expect_type="text/html")

    via_config, h_config = Configuration.extract_from_params(request.params)

    rewriter = LXMLRewriter(
        static_url=context.static_proxy_url_for(""),
        route_url=request.route_url,
        h_config=h_config,
    )

    with timeit("rewriting total"):
        doc.content = rewriter.rewrite(doc)

    return doc.response()
