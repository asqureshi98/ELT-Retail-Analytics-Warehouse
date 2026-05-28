from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOC_PATHS = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def _slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[`*_{}\[\]().,!?;:'\"/\\]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9_-]", "", text)
    return text


def _anchors(markdown: str) -> set[str]:
    counts: dict[str, int] = {}
    anchors = set()
    for match in HEADING_RE.finditer(markdown):
        base = _slug(match.group(2))
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def _iter_markdown_links(markdown: str):
    for regex in (LINK_RE, IMG_RE):
        for match in regex.finditer(markdown):
            target = match.group(1).strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            yield target


def test_internal_markdown_links_and_assets_exist() -> None:
    missing: list[str] = []
    for path in DOC_PATHS:
        markdown = path.read_text(encoding="utf-8")
        for raw_target in _iter_markdown_links(markdown):
            target = raw_target.split()[0]
            parsed = urlparse(target)
            if parsed.scheme in {"http", "https", "mailto"}:
                continue
            if target.startswith("#"):
                destination = path
                fragment = unquote(target[1:])
            else:
                target_path, _, fragment = target.partition("#")
                destination = (path.parent / unquote(target_path)).resolve()
            try:
                destination.relative_to(ROOT)
            except ValueError:
                missing.append(f"{path.relative_to(ROOT)} -> {raw_target} escapes repository")
                continue
            if not destination.exists():
                missing.append(f"{path.relative_to(ROOT)} -> {raw_target} missing file")
                continue
            if fragment and destination.suffix.lower() == ".md":
                anchors = _anchors(destination.read_text(encoding="utf-8"))
                if fragment not in anchors:
                    missing.append(f"{path.relative_to(ROOT)} -> {raw_target} missing anchor")
    assert not missing, "Broken documentation links:\n" + "\n".join(sorted(missing))


def test_portfolio_assets_are_lightweight_and_renderable() -> None:
    assets_dir = ROOT / "docs" / "assets"
    required_assets = {
        "architecture.svg",
        "elt_flow.svg",
        "dimensional_model.svg",
        "README.md",
    }
    assert assets_dir.is_dir()
    assert required_assets.issubset({path.name for path in assets_dir.iterdir()})

    for svg in assets_dir.glob("*.svg"):
        content = svg.read_text(encoding="utf-8")
        assert content.lstrip().startswith("<svg")
        assert "<title" in content
        assert svg.stat().st_size < 100_000
