import hashlib
import urllib.parse as urllib


def normalize_url(url: str) -> str:
    scheme, netloc, path, _, _ = urllib.urlsplit(url)
    path = urllib.quote(path, "/%")
    return urllib.urlunsplit((scheme, netloc, path, "", ""))


def hashsum(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def extract_domain(url: str) -> str:
    scheme, netloc, path, qs, anchor = urllib.urlsplit(url)
    return netloc


def absolute_url(root: str, relative: str) -> str:
    if relative.startswith(("http://", "https://")):
        return relative

    if not root.startswith(("http://", "https://")):
        root = "https://" + root

    root = root.removesuffix("/")
    relative = "/" + relative.removeprefix("/")

    return root + relative
