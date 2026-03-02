from __future__ import annotations

import re


def parse_links_from_html(
    html: str,
    *,
    base_url: str = "",
    pattern: str = r"\.xlsx?|\.pdf|\.csv",
    dedup: bool = True,
) -> list[dict[str, str]]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    links: list[dict[str, str]] = []
    seen: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href = str(a_tag["href"])
        if not re.search(pattern, href, re.IGNORECASE):
            continue

        if dedup:
            if href in seen:
                continue
            seen.add(href)

        full_url = href
        if full_url.startswith("/") and base_url:
            full_url = f"{base_url}{full_url}"

        text = a_tag.get_text(strip=True)
        if not text:
            filename = href.split("/")[-1]
            text = re.sub(r"\.\w+$", "", filename).replace("-", " ")

        links.append({"url": full_url, "text": text})

    return links
