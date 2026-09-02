"""Keyword search over the store policy manual.

The manual is eight pages split into ten numbered sections, so the document
already tells us where the chunk boundaries are. Section-level chunks plus BM25
answer the questions this store actually gets, with no embedding service and no
index to keep in sync.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader
from rank_bm25 import BM25Okapi

from . import config
from .text import stem

HEADING = re.compile(r"^(\d{1,2})(?:\.(\d{1,2}))?\.?\s+([A-ZÀ-Ú].{2,70})$")
RUNNING_HEADER = re.compile(
    r"^(Empório da Música Manual de Políticas e Procedimentos|Página \d+)$"
)


@dataclass
class Section:
    number: str
    title: str
    text: str
    parent: str = ""

    @property
    def reference(self) -> str:
        if self.parent and not self.parent.endswith(self.title):
            return f"{self.number} {self.title} (em {self.parent})"
        return f"{self.number} {self.title}"

    @property
    def indexed_text(self) -> str:
        return f"{self.parent} {self.title} {self.title} {self.text}"


def _lines(pdf_path: Path) -> list[str]:
    reader = PdfReader(pdf_path)
    lines = []
    for page in reader.pages:
        raw = page.extract_text(extraction_mode="layout") or ""
        for line in raw.splitlines():
            line = re.sub(r"\s+", " ", line).strip()
            if line and not RUNNING_HEADER.match(line):
                lines.append(line)
    return lines


def extract_sections(pdf_path: Path) -> list[Section]:
    """Split the manual on its own numbering.

    Section 7.2 contains a numbered list that looks exactly like a heading, so a
    candidate is only accepted when it continues the sequence: after 7.1 the
    document can open 7.2 or 8, never a fresh 1.
    """
    sections: list[Section] = []
    top = sub = 0
    number = title = None
    parent = ""
    buffer: list[str] = []

    def flush():
        if number and buffer:
            sections.append(Section(number, title, " ".join(buffer).strip(), parent))

    for line in _lines(pdf_path):
        match = HEADING.match(line)
        if match:
            major, minor, heading = int(match.group(1)), match.group(2), match.group(3)
            starts_section = minor is None and major == top + 1
            starts_subsection = minor is not None and major == top and int(minor) == sub + 1
            if starts_section or starts_subsection:
                flush()
                if starts_section:
                    top, sub = major, 0
                    number = f"{top}."
                    # A top level heading with no body of its own only exists to
                    # name its subsections, so it is carried down instead of lost.
                    parent = f"{top}. {heading.strip()}"
                else:
                    sub = int(minor)
                    number = f"{top}.{sub}"
                title, buffer = heading.strip(), []
                continue
        buffer.append(line)

    flush()
    return sections


class PolicyIndex:
    def __init__(self, sections: list[Section]):
        self.sections = sections
        # The title is repeated in the indexed text so a question phrased like the
        # heading ranks that section up.
        self._bm25 = BM25Okapi([stem(section.indexed_text) for section in sections])

    def search(self, question: str, limit: int = 3) -> list[dict]:
        tokens = stem(question)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(zip(self.sections, scores), key=lambda pair: pair[1], reverse=True)
        return [
            {"section": section.reference, "score": round(float(score), 3), "text": section.text}
            for section, score in ranked[:limit]
            if score > 0
        ]

    def table_of_contents(self) -> list[str]:
        return [section.reference for section in self.sections]


@lru_cache(maxsize=1)
def load(pdf_path: Path | None = None) -> PolicyIndex:
    return PolicyIndex(extract_sections(pdf_path or config.POLICY_PDF))
