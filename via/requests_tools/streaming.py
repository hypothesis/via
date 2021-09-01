def stream_bytes(response, min_chunk_size=64000):
    """Stream content from a `requests.Response` object.

    The response must have been called with `stream=True` for this to be
    effective. This will attempt to smooth over some of the variation of block
    size to give a smoother output for upstream services calling us.
    """
    buffer = b""

    # The chunk_size appears to be a guide value at best. We often get more
    # or just about 9 bytes, so we'll do some smoothing for our callers so we
    # don't incur overhead with very short iterations of content
    for chunk in response.iter_content(chunk_size=min_chunk_size):
        buffer += chunk
        if len(buffer) >= min_chunk_size:
            yield buffer
            buffer = b""

    if buffer:
        yield buffer
