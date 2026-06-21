from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class ParsedDocument:
    filename: str
    text: str
    html: str


DOWNLOAD_CACHE: dict[str, dict[str, str]] = {}


def parse_uploaded_document(filename: str, body: bytes) -> ParsedDocument:
    suffix = Path(filename).suffix.lower()
    if suffix not in {"", ".txt", ".md", ".markdown"}:
        raise ValueError("Unsupported document type. Supported types: .txt, .md, .markdown")

    text = body.decode("utf-8")
    html_content = text_to_block_html(text)
    return ParsedDocument(filename=filename, text=text, html=html_content)


def text_to_block_html(text: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        return ""
    blocks: list[str] = []
    for paragraph in paragraphs:
        block_id = f"moss-block-{uuid4().hex}"
        escaped = html.escape(paragraph)
        blocks.append(f'<div id="{block_id}"><p>{escaped}</p></div>')
    return "\n".join(blocks)


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return cleaned or "moss-document"


def save_document(storage_dir: str | Path, doc_id: str, content: str) -> None:
    safe_doc_id = safe_filename(doc_id)
    document_dir = Path(storage_dir) / "documents"
    document_dir.mkdir(parents=True, exist_ok=True)

    html_path = document_dir / f"{safe_doc_id}.html"
    meta_path = document_dir / f"{safe_doc_id}.json"
    html_path.write_text(content, encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {"docId": doc_id, "savedAt": datetime.now(timezone.utc).isoformat()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def prepare_download_artifact(export_format: str, content: str) -> str:
    token = uuid4().hex
    DOWNLOAD_CACHE[token] = {"format": export_format, "content": content}
    return token


def get_download_artifact(token: str) -> dict[str, str] | None:
    return DOWNLOAD_CACHE.get(token)


def html_to_markdown(content: str) -> str:
    parser = _MarkdownHtmlParser()
    parser.feed(content)
    parser.close()
    return parser.render()


class _MarkdownHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self._buffer: list[str] = []
        self._block_tag: str | None = None
        self._heading_level: int | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if re.fullmatch(r"h[1-6]", normalized):
            self._flush_buffer()
            self._block_tag = normalized
            self._heading_level = int(normalized[1])
            self._buffer = []
        elif normalized in {"p", "li", "blockquote"}:
            self._flush_buffer()
            self._block_tag = normalized
            self._heading_level = None
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if self._block_tag == normalized:
            self._flush_buffer()
            self._block_tag = None
            self._heading_level = None

    def handle_data(self, data: str) -> None:
        self._buffer.append(data)

    def render(self) -> str:
        self._flush_buffer()
        return "\n\n".join(line for line in self.lines if line).strip() + "\n"

    def _flush_buffer(self) -> None:
        text = " ".join(" ".join(self._buffer).split())
        if not text:
            self._buffer = []
            return
        if self._heading_level is not None:
            self.lines.append(f"{'#' * self._heading_level} {text}")
        elif self._block_tag == "li":
            self.lines.append(f"- {text}")
        elif self._block_tag == "blockquote":
            self.lines.append(f"> {text}")
        else:
            self.lines.append(text)
        self._buffer = []
