from __future__ import absolute_import, print_function, division

from ... import utils
import itertools
from ...exceptions import HttpException
from .. import CONTENT_MISSING


def assemble_request(request):
    if request.content == CONTENT_MISSING:
        raise HttpException("Cannot assemble flow with CONTENT_MISSING")
    head = assemble_request_head(request)
    body = b"".join(assemble_body(request.headers, [request.data.content]))
    return head + body


def assemble_request_head(request):
    first_line = _assemble_request_line(request.data)
    headers = _assemble_request_headers(request.data)
    return b"%s\r\n%s\r\n" % (first_line, headers)


def assemble_response(response):
    if response.content == CONTENT_MISSING:
        raise HttpException("Cannot assemble flow with CONTENT_MISSING")
    head = assemble_response_head(response)
    body = b"".join(assemble_body(response.headers, [response.content]))
    return head + body


def assemble_response_head(response):
    first_line = _assemble_response_line(response)
    headers = _assemble_response_headers(response)
    return b"%s\r\n%s\r\n" % (first_line, headers)


def assemble_body(headers, body_chunks):
    if "chunked" in headers.get("transfer-encoding", "").lower():
        for chunk in body_chunks:
            if chunk:
                yield b"%x\r\n%s\r\n" % (len(chunk), chunk)
        yield b"0\r\n\r\n"
    else:
        for chunk in body_chunks:
            yield chunk


def _assemble_request_line(request_data):
    """
    Args:
        request_data (netlib.http.request.RequestData)
    """
    form = request_data.first_line_format
    if form == "relative":
        return b"%s %s %s" % (
            request_data.method,
            request_data.path,
            request_data.http_version
        )
    elif form == "authority":
        return b"%s %s:%d %s" % (
            request_data.method,
            request_data.host,
            request_data.port,
            request_data.http_version
        )
    elif form == "absolute":
        return b"%s %s://%s:%d%s %s" % (
            request_data.method,
            request_data.scheme,
            request_data.host,
            request_data.port,
            request_data.path,
            request_data.http_version
        )
    else:
        raise RuntimeError("Invalid request form")


def _assemble_request_headers(request_data):
    """
    Args:
        request_data (netlib.http.request.RequestData)
    """
    headers = request_data.headers.copy()
    if "host" not in headers and request_data.scheme and request_data.host and request_data.port:
        headers["host"] = utils.hostport(
            request_data.scheme,
            request_data.host,
            request_data.port
        )
    return bytes(headers)


def _assemble_response_line(response):
    return b"%s %d %s" % (
        response.http_version,
        response.status_code,
        response.msg,
    )


def _assemble_response_headers(response):
    return bytes(response.headers)
