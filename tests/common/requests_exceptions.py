import json
from io import BytesIO

from requests import Response


def make_requests_exception(
    error_class, status_code, json_data=None, raw_data=None, **response_kwargs
):
    response = Response()
    response.status_code = status_code

    for key, value in response_kwargs.items():
        setattr(response, key, value)

    if raw_data:
        response.raw = BytesIO(raw_data.encode("utf-8"))

    elif json_data:
        response.raw = BytesIO(json.dumps(json_data).encode("utf-8"))

    return error_class(response=response)
