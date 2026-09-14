"""Validation and streaming downloads for allowed HTTPS hosts."""

import ipaddress
import socket
import time
from urllib.parse import urlparse

from ..config import allowed_url_hosts


def validate_url(url: str, resolve=True):
    """Accept only configured public hosts without credentials or redirects."""
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in allowed_url_hosts()
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError(
            "Use an HTTPS video URL from an allowed host, or upload the file."
        )
    if resolve:
        validate_public_host(parsed.hostname)


def validate_public_host(host: str):
    """Reject a trusted hostname if it currently resolves to a private address."""
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(
        not ipaddress.ip_address(item[4][0]).is_global for item in addresses
    ):
        raise ValueError("Private network video URLs are not allowed.")


def download_url(url, path):
    """Stream an allowed source to disk within the download deadline."""
    import requests

    validate_url(url)
    deadline = time.monotonic() + 90
    with requests.get(
        url, stream=True, timeout=(5, 15), allow_redirects=False
    ) as response:
        if response.status_code != 200:
            raise ValueError(
                "The video URL could not be downloaded. Upload the file instead."
            )
        with path.open("wb") as output:
            for chunk in response.iter_content(65536):
                if time.monotonic() > deadline:
                    raise ValueError(
                        "Video download timed out. Please retry or upload the file."
                    )
                output.write(chunk)
