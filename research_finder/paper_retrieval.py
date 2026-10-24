"""Legitimate paper retrieval with explicit abstract-only fallback."""
from __future__ import annotations
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from .models import Paper

@dataclass(frozen=True)
class RetrievedPaper:
    paper: Paper
    source_url: str | None
    text: str
    status: str
    extraction: str
    sections: tuple[tuple[str, str], ...] = ()
    pages_available: bool = False

    @property
    def full_text_available(self) -> bool:
        return bool(self.text.strip()) and self.status == "full-text"

class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "nav", "header", "footer"}: self.skip += 1
    def handle_endtag(self, tag):
        if tag in {"script", "style", "nav", "header", "footer"}: self.skip = max(0, self.skip - 1)
    def handle_data(self, data):
        if not self.skip and data.strip(): self.parts.append(data.strip())

def _extract_html(data: bytes) -> str:
    parser = _HTMLText()
    parser.feed(data.decode("utf-8", errors="replace"))
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()

def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        import io
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages).strip()
    except ImportError:
        # Basic fallback for environments without an optional PDF extractor.
        chunks = re.findall(rb"\(([^()] {20,})\)", data)
        return re.sub(r"\s+", " ", b" ".join(chunks).decode("latin-1", errors="ignore")).strip()
    except Exception:
        return ""

class PaperRetriever:
    def __init__(self, cache_dir: str | Path = ".research_cache", timeout: float = 20, opener=urlopen):
        self.cache_dir, self.timeout, self.opener = Path(cache_dir), timeout, opener

    def retrieve(self, paper: Paper) -> RetrievedPaper:
        urls = []
        if paper.oa_pdf_url: urls.append(paper.oa_pdf_url)
        if paper.url and paper.url not in urls: urls.append(paper.url)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        for url in urls:
            key = hashlib.sha256(url.encode()).hexdigest()
            cache = self.cache_dir / key
            try:
                if cache.with_suffix(".txt").is_file():
                    text = cache.with_suffix(".txt").read_text(encoding="utf-8")
                    return self._result(paper, url, text, "cached")
                request = Request(url, headers={"User-Agent": "research-finder/0.1"})
                with self.opener(request, timeout=self.timeout) as response:
                    data = response.read()
                    content_type = response.headers.get("Content-Type", "").lower()
                text = _extract_pdf(data) if url.lower().split("?")[0].endswith(".pdf") or "pdf" in content_type else _extract_html(data)
                if text:
                    cache.with_suffix(".txt").write_text(text, encoding="utf-8")
                    return self._result(paper, url, text, "full-text")
            except (HTTPError, URLError, TimeoutError, OSError):
                continue
        status = "abstract-only" if paper.abstract else "unavailable"
        return RetrievedPaper(paper, None, paper.abstract, status, "openalex-abstract" if paper.abstract else "metadata")

    def _result(self, paper, url, text, extraction):
        sections = tuple((heading, body) for heading, body in re.findall(
            r"(?im)^\s*(Abstract|Introduction|Related Work|Methods?|Results?|Discussion|Conclusion)\s*$([\s\S]*?)(?=^\s*(?:Abstract|Introduction|Related Work|Methods?|Results?|Discussion|Conclusion)\s*$|\Z)",
            text))
        return RetrievedPaper(paper, url, text, "full-text", extraction, sections, False)
