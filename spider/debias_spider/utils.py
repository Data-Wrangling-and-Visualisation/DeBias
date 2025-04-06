import hashlib
import urllib.parse as urllib
import urllib.parse as urlparse


def normalize_url(url: str) -> str:
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(url)
    path = urllib.quote(path, "/%")
    qs = urllib.quote_plus(qs, ":&=")
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))


def hashsum(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def extract_domain(url: str) -> str:
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(url)
    return netloc


def absolute_url(root: str, relative: str) -> str:
    if relative.startswith(("http://", "https://")):
        return relative

    if not root.startswith(("http://", "https://")):
        root = "https://" + root

    root = root.removesuffix("/")
    relative = "/" + relative.removeprefix("/")

    return root + relative
