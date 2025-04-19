import hashlib
import urllib.parse as urllib
from typing import Literal

from bs4 import BeautifulSoup

from debias.core.configs import TargetConfig


class Parser:
    def __init__(self, config: TargetConfig) -> None:
        self._target_config = config
        self._target_id = config.id
        self._target_name = config.name
        self._target_domain = extract_domain(config.root.encoded_string())
        self._target_render: Literal["auto", "always", "never"] = config.render
        self._text_selector = config.text_selector
        self._href_selector = config.href_selector
        self._href_domain_only = config.domain_only

    @property
    def domain(self) -> str:
        return self._target_domain

    @property
    def need_render(self) -> Literal["auto", "always", "never"]:
        return self._target_render

    @property
    def config(self) -> TargetConfig:
        return self._target_config

    def extract_text(self, html_content: str, logger) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        elements = soup.select(self._text_selector)
        if not elements:
            logger.warning("no text content found")
            return ""
        return " ".join([element.get_text(strip=True) for element in elements])

    def extract_hrefs(self, html_content: str, logger) -> list[str]:
        soup = BeautifulSoup(html_content, "html.parser")
        elements = soup.select(self._href_selector)
        hrefs = []

        failed = []

        for element in elements:
            href = element.get("href")
            if not isinstance(href, str) or len(href) == 0:
                failed.append(href)
                continue

            if not self._href_domain_only:
                hrefs.append(absolute_url(self._target_domain, href))
                continue

            href_domain = extract_domain(href)
            if href_domain == self._target_domain:
                hrefs.append(absolute_url(self._target_domain, href))

        if failed:
            logger.warning(f"failed to extract multiple sources: {failed}")

        return hrefs


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
