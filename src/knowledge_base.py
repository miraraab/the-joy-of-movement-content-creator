# src/knowledge_base.py
"""
knowledge_base.py
=================
Thin wrapper around DocumentProcessor.
Provides a clean, named API for the content pipeline.

Usage:
    kb = KnowledgeBaseManager()
    primary_ctx   = kb.get_primary_context()
    secondary_ctx = kb.get_secondary_context()
    hybrid_ctx    = kb.get_hybrid_context()
"""

from document_processor import DocumentProcessor, Document, KnowledgeBase


class KnowledgeBaseManager:
    """
    Single entry point for all knowledge base operations.
    Caches documents after first load to avoid repeated disk reads.
    """

    def __init__(self, kb_root: str = "knowledge_base", max_chars_per_doc: int = None):
        self._processor = DocumentProcessor(
            kb_root=kb_root,
            max_chars_per_doc=max_chars_per_doc,
        )
        self._kb: KnowledgeBase = None  # lazy load

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load(self) -> KnowledgeBase:
        """Load all documents (cached after first call)."""
        if self._kb is None:
            self._kb = self._processor.load_all()
        return self._kb

    def get_primary_docs(self) -> list[Document]:
        return self.load().primary

    def get_secondary_docs(self) -> list[Document]:
        return self.load().secondary

    def get_all_docs(self) -> list[Document]:
        return self.load().all_documents()

    # ------------------------------------------------------------------
    # Context strings (prompt-ready)
    # ------------------------------------------------------------------

    def get_primary_context(self) -> str:
        """Brand guidelines, product specs, past content → prompt block."""
        return self._processor.get_context_block(
            self.get_primary_docs(),
            label="PRIMARY KNOWLEDGE BASE – Joy of Movement",
        )

    def get_secondary_context(self) -> str:
        """Market trends, competitor analysis → prompt block."""
        return self._processor.get_context_block(
            self.get_secondary_docs(),
            label="SECONDARY RESEARCH LAYER – Industry Context",
        )

    def get_hybrid_context(self) -> str:
        """Both knowledge bases combined for hybrid prompt templates."""
        return self._processor.get_context_block(
            self.get_all_docs(),
            label="FULL KNOWLEDGE BASE – Brand + Industry",
        )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def summary(self) -> str:
        kb = self.load()
        return kb.summary()

    def token_estimate(self) -> dict:
        p = self._processor.estimate_tokens(self.get_primary_context())
        s = self._processor.estimate_tokens(self.get_secondary_context())
        return {"primary": p, "secondary": s, "combined": p + s}


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    kb = KnowledgeBaseManager(kb_root="knowledge_base")

    print(kb.summary())
    print("\n--- Token Estimates ---")
    for k, v in kb.token_estimate().items():
        print(f"  {k}: ~{v:,} tokens")

    print("\n--- Primary Context (first 300 chars) ---")
    print(kb.get_primary_context()[:300])

    print("\n--- Secondary Context (first 300 chars) ---")
    print(kb.get_secondary_context()[:300])