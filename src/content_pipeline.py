"""
content_pipeline.py
===================
Orchestrates the full content creation workflow:
Document → Monitor → Brief → Publish → Iterate

Each stage is explicit and can be run independently or as a full pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from document_processor import DocumentProcessor
from prompt_templates import PromptTemplates, PromptResult, TemplateType, ContentType
from llm_integration import LLMIntegration


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ContentBrief:
    """Defines what content to create before generation starts."""
    topic: str
    content_type: ContentType
    template_type: TemplateType
    target_audience: str = "55+ German adults in life transition"
    key_message: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ContentOutput:
    """Holds generated content and its full audit trail."""
    brief: ContentBrief
    generated_text: str
    template_type: str
    content_type: str
    topic: str
    char_count: int = 0
    approved: bool = False
    feedback: str = ""
    iteration: int = 1
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        self.char_count = len(self.generated_text)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class ContentPipeline:
    """
    Runs the full content creation pipeline:
    1. Document  – load and parse knowledge base
    2. Monitor   – report on what's loaded
    3. Brief     – define what to create
    4. Publish   – generate content via LLM
    5. Iterate   – refine based on feedback
    """

    def __init__(self, kb_root: str = "knowledge_base"):
        self.processor = DocumentProcessor(kb_root=kb_root)
        self.templates = PromptTemplates()
        self.llm = LLMIntegration()

        # State
        self.kb = None
        self.primary_context = ""
        self.secondary_context = ""
        self.history: list[ContentOutput] = []

    # ------------------------------------------------------------------
    # Stage 1: Document
    # ------------------------------------------------------------------

    def stage_document(self) -> None:
        """Load and parse all knowledge base documents."""
        print("\n" + "=" * 60)
        print("STAGE 1: DOCUMENT")
        print("=" * 60)

        self.kb = self.processor.load_all()
        self.primary_context = self.processor.get_context_block(
            self.kb.primary, label="PRIMARY KNOWLEDGE BASE"
        )
        self.secondary_context = self.processor.get_context_block(
            self.kb.secondary, label="SECONDARY RESEARCH"
        )
        print("[OK] Knowledge base ready for pipeline.")

    # ------------------------------------------------------------------
    # Stage 2: Monitor
    # ------------------------------------------------------------------

    def stage_monitor(self) -> dict:
        """Analyze loaded knowledge base and report status."""
        print("\n" + "=" * 60)
        print("STAGE 2: MONITOR")
        print("=" * 60)

        if not self.kb:
            print("[WARN] No knowledge base loaded. Run stage_document() first.")
            return {}

        primary_docs = [d.filename for d in self.kb.primary]
        secondary_docs = [d.filename for d in self.kb.secondary]
        primary_tokens = self.processor.estimate_tokens(self.primary_context)
        secondary_tokens = self.processor.estimate_tokens(self.secondary_context)

        report = {
            "primary_docs": primary_docs,
            "secondary_docs": secondary_docs,
            "primary_tokens": primary_tokens,
            "secondary_tokens": secondary_tokens,
            "total_tokens": primary_tokens + secondary_tokens,
            "content_generated_this_session": len(self.history),
        }

        print(f"Primary docs:    {primary_docs}")
        print(f"Secondary docs:  {secondary_docs}")
        print(f"Primary tokens:  ~{primary_tokens:,}")
        print(f"Secondary tokens:~{secondary_tokens:,}")
        print(f"Total tokens:    ~{report['total_tokens']:,}")
        print(f"Content generated this session: {len(self.history)}")

        return report

    # ------------------------------------------------------------------
    # Stage 3: Brief
    # ------------------------------------------------------------------

    def stage_brief(
        self,
        topic: str,
        content_type: ContentType,
        template_type: TemplateType,
        key_message: str = "",
        notes: str = "",
    ) -> ContentBrief:
        """Define the content brief before generation."""
        print("\n" + "=" * 60)
        print("STAGE 3: BRIEF")
        print("=" * 60)

        brief = ContentBrief(
            topic=topic,
            content_type=content_type,
            template_type=template_type,
            key_message=key_message,
            notes=notes,
        )

        print(f"Topic:        {brief.topic}")
        print(f"Format:       {brief.content_type.value}")
        print(f"Template:     {brief.template_type.value}")
        print(f"Key message:  {brief.key_message or '(none specified)'}")
        print(f"Notes:        {brief.notes or '(none)'}")
        print("[OK] Brief created.")

        return brief

    # ------------------------------------------------------------------
    # Stage 4: Publish
    # ------------------------------------------------------------------

    def stage_publish(self, brief: ContentBrief) -> ContentOutput:
        """Generate content from brief using LLM."""
        print("\n" + "=" * 60)
        print("STAGE 4: PUBLISH")
        print("=" * 60)

        if not self.kb:
            raise RuntimeError("Knowledge base not loaded. Run stage_document() first.")

        # Inject key message into topic if provided
        topic = brief.topic
        if brief.key_message:
            topic = f"{brief.topic} (key message: {brief.key_message})"
        if brief.notes:
            topic = f"{topic} | Notes: {brief.notes}"

        prompt: PromptResult = self.templates.build(
            template_type=brief.template_type,
            content_type=brief.content_type,
            topic=topic,
            primary_context=self.primary_context,
            secondary_context=self.secondary_context,
        )

        generated_text = self.llm.generate(prompt)

        output = ContentOutput(
            brief=brief,
            generated_text=generated_text,
            template_type=brief.template_type.value,
            content_type=brief.content_type.value,
            topic=brief.topic,
            iteration=1,
        )

        self.history.append(output)

        print("\n" + "-" * 60)
        print("GENERATED CONTENT:")
        print("-" * 60)
        print(generated_text)
        print("-" * 60)
        print(f"[OK] {output.char_count} chars generated.")

        return output

    # ------------------------------------------------------------------
    # Stage 5: Iterate
    # ------------------------------------------------------------------

    def stage_iterate(
        self,
        previous: ContentOutput,
        feedback: str,
    ) -> ContentOutput:
        """
        Refine content based on feedback.
        Appends feedback to the prompt and regenerates.
        """
        print("\n" + "=" * 60)
        print("STAGE 5: ITERATE")
        print("=" * 60)
        print(f"Feedback: {feedback}")

        # Add feedback to notes for next iteration
        refined_brief = ContentBrief(
            topic=previous.brief.topic,
            content_type=previous.brief.content_type,
            template_type=previous.brief.template_type,
            key_message=previous.brief.key_message,
            notes=(
                f"PREVIOUS VERSION:\n{previous.generated_text}\n\n"
                f"FEEDBACK TO INCORPORATE:\n{feedback}\n\n"
                f"Generate an improved version that addresses this feedback."
            ),
        )

        output = self.stage_publish(refined_brief)
        output.iteration = previous.iteration + 1
        output.feedback = feedback

        print(f"[OK] Iteration {output.iteration} complete.")
        return output

    # ------------------------------------------------------------------
    # Full pipeline (convenience method)
    # ------------------------------------------------------------------

    def run(
        self,
        topic: str,
        content_type: ContentType = ContentType.SOCIAL_MEDIA,
        template_type: TemplateType = TemplateType.HYBRID,
        key_message: str = "",
    ) -> ContentOutput:
        """
        Run the full pipeline in one call.
        Stages: Document → Monitor → Brief → Publish
        (Iterate is manual – call stage_iterate() after reviewing output)
        """
        self.stage_document()
        self.stage_monitor()
        brief = self.stage_brief(
            topic=topic,
            content_type=content_type,
            template_type=template_type,
            key_message=key_message,
        )
        return self.stage_publish(brief)


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pipeline = ContentPipeline(kb_root="knowledge_base")

    # Run full pipeline
    output = pipeline.run(
        topic="Why community matters more than fitness after 60",
        content_type=ContentType.SOCIAL_MEDIA,
        template_type=TemplateType.HYBRID,
        key_message="Belonging is the product, movement is the vehicle",
    )

    print(f"\n[PIPELINE COMPLETE]")
    print(f"Topic:     {output.topic}")
    print(f"Format:    {output.content_type}")
    print(f"Template:  {output.template_type}")
    print(f"Chars:     {output.char_count}")
    print(f"Iteration: {output.iteration}")