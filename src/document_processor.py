"""
document_processor.py
=====================
Ingests and parses markdown documents from the Joy of Movement
knowledge base. Returns structured content ready for prompt injection.

No vector store. No embeddings. Files → parsed text → prompt context.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import markdown


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Document:
    """A single parsed knowledge base document."""
    filename: str
    category: str           # "primary" or "secondary"
    raw_text: str           # Original markdown text
    plain_text: str         # Stripped of markdown syntax
    char_count: int = 0
    source_path: str = ""

    def __post_init__(self):
        self.char_count = len(self.plain_text)


@dataclass
class KnowledgeBase:
    """Holds all loaded documents, split by category."""
    primary: list[Document] = field(default_factory=list)
    secondary: list[Document] = field(default_factory=list)

    def all_documents(self) -> list[Document]:
        return self.primary + self.secondary

    def summary(self) -> str:
        return (
            f"Knowledge Base loaded: "
            f"{len(self.primary)} primary, "
            f"{len(self.secondary)} secondary documents | "
            f"Total chars: {sum(d.char_count for d in self.all_documents())}"
        )


# ---------------------------------------------------------------------------
# Core processor
# ---------------------------------------------------------------------------

class DocumentProcessor:
    """
    Reads markdown files from knowledge_base/primary/ and /secondary/.
    Strips markdown to plain text for prompt injection.
    Optionally truncates documents to stay within token budgets.
    """

    # Rough chars-per-token estimate for Claude (conservative)
    CHARS_PER_TOKEN = 4

    def __init__(
        self,
        kb_root: str = "knowledge_base",
        max_chars_per_doc: Optional[int] = None,
    ):
        """
        Args:
            kb_root:           Path to knowledge_base/ directory.
            max_chars_per_doc: Hard cap per document (None = no cap).
                               Useful for token budget control.
        """
        self.kb_root = Path(kb_root)
        self.max_chars_per_doc = max_chars_per_doc
        self._md_converter = markdown.Markdown()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_all(self) -> KnowledgeBase:
        """Load and parse all documents from both knowledge bases."""
        kb = KnowledgeBase()

        for category in ("primary", "secondary"):
            folder = self.kb_root / category
            if not folder.exists():
                print(f"[WARN] Folder not found, skipping: {folder}")
                continue

            docs = self._load_folder(folder, category)
            if category == "primary":
                kb.primary = docs
            else:
                kb.secondary = docs

        print(kb.summary())
        return kb

    def load_category(self, category: str) -> list[Document]:
        """Load a single category ('primary' or 'secondary')."""
        folder = self.kb_root / category
        if not folder.exists():
            raise FileNotFoundError(f"Knowledge base folder not found: {folder}")
        return self._load_folder(folder, category)

    def get_context_block(
        self,
        docs: list[Document],
        label: str = "KNOWLEDGE BASE",
        separator: str = "\n\n---\n\n",
    ) -> str:
        """
        Concatenate documents into a single prompt-ready context string.

        Args:
            docs:      List of Document objects to concatenate.
            label:     Header label for the context block.
            separator: String inserted between documents.

        Returns:
            Formatted string ready for injection into a prompt.
        """
        if not docs:
            return f"[{label}: No documents loaded]"

        parts = [f"=== {label} ===\n"]
        for doc in docs:
            header = f"[{doc.filename} | {doc.category}]"
            parts.append(f"{header}\n{doc.plain_text}")

        return separator.join(parts)

    def estimate_tokens(self, text: str) -> int:
        """Rough token count estimate (chars / 4)."""
        return len(text) // self.CHARS_PER_TOKEN

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_folder(self, folder: Path, category: str) -> list[Document]:
        """Recursively load all .md files from a folder."""
        docs = []
        md_files = sorted(folder.rglob("*.md"))

        if not md_files:
            print(f"[WARN] No .md files found in: {folder}")
            return docs

        for filepath in md_files:
            doc = self._parse_file(filepath, category)
            if doc:
                docs.append(doc)
                print(f"[OK]   Loaded: {filepath.relative_to(self.kb_root)}"
                      f" ({doc.char_count} chars)")

        return docs

    def _parse_file(self, filepath: Path, category: str) -> Optional[Document]:
        """Read and parse a single markdown file."""
        try:
            raw_text = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"[ERROR] Could not read {filepath}: {e}")
            return None

        plain_text = self._strip_markdown(raw_text)

        if self.max_chars_per_doc:
            plain_text = plain_text[: self.max_chars_per_doc]

        return Document(
            filename=filepath.name,
            category=category,
            raw_text=raw_text,
            plain_text=plain_text,
            source_path=str(filepath),
        )

    def _strip_markdown(self, text: str) -> str:
        """
        Convert markdown to plain text.
        Uses the `markdown` library to render HTML, then strips tags.
        Falls back to raw text if parsing fails.
        """
        try:
            # Reset converter state between calls
            self._md_converter.reset()
            html = self._md_converter.convert(text)
            # Remove HTML tags with a simple approach (no extra deps)
            plain = self._remove_html_tags(html)
            # Clean up excess whitespace
            lines = [line.strip() for line in plain.splitlines()]
            plain = "\n".join(line for line in lines if line)
            return plain
        except Exception:
            # Graceful fallback: return raw markdown
            return text

    @staticmethod
    def _remove_html_tags(html: str) -> str:
        """Strip HTML tags without importing extra libraries."""
        result = []
        in_tag = False
        for char in html:
            if char == "<":
                in_tag = True
            elif char == ">":
                in_tag = False
                result.append(" ")  # tag → space keeps words from merging
            elif not in_tag:
                result.append(char)
        return "".join(result)


# ---------------------------------------------------------------------------
# Quick test – run directly to verify setup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    processor = DocumentProcessor(
        kb_root="knowledge_base",
        max_chars_per_doc=None,  # No cap during development
    )

    kb = processor.load_all()

    print("\n--- PRIMARY CONTEXT PREVIEW (first 500 chars) ---")
    primary_context = processor.get_context_block(kb.primary, label="PRIMARY KNOWLEDGE BASE")
    print(primary_context[:500])

    print("\n--- SECONDARY CONTEXT PREVIEW (first 500 chars) ---")
    secondary_context = processor.get_context_block(kb.secondary, label="SECONDARY RESEARCH")
    print(secondary_context[:500])

    print(f"\n--- TOKEN ESTIMATES ---")
    print(f"Primary:   ~{processor.estimate_tokens(primary_context):,} tokens")
    print(f"Secondary: ~{processor.estimate_tokens(secondary_context):,} tokens")
    print(f"Combined:  ~{processor.estimate_tokens(primary_context + secondary_context):,} tokens")