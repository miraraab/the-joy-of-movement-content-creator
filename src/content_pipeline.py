"""
content_pipeline.py
===================
Orchestrates the full content creation workflow:
Document → Monitor → Brief → Publish → Iterate

Each stage is explicit and can be run independently or as a full pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

from document_processor import DocumentProcessor
from prompt_templates import PromptTemplates, PromptResult, TemplateType, ContentType
from llm_integration import LLMIntegration


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ScoreIssue:
    """Single issue with problem & improvement suggestion."""
    problem: str
    suggestion: str


@dataclass
class ContentScore:
    """Evaluates generated content against 4 brand dimensions."""
    emotional_truth: float  # 1-10: Real emotion vs manufactured
    differentiation: float  # 1-10: Unique to JOM vs generic
    brand_integrity: float  # 1-10: Unmistakably Joy of Movement
    authenticity: float     # 1-10: No corporate speak, forbidden words
    overall_score: float    # Average of above 4
    strengths: list = field(default_factory=list)
    weaknesses: list = field(default_factory=list)


@dataclass
class ContentBrief:
    """Defines what content to create before generation starts."""
    topic: str
    content_type: ContentType
    template_type: TemplateType
    target_audience: str = "55+ German adults in life transition"
    key_message: str = ""
    notes: str = ""
    desired_versions: list = field(default_factory=lambda: ["blog_post", "social_media", "newsletter"])
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
    score: Optional[ContentScore] = None

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
    # Helper: Interactive version selection
    # ------------------------------------------------------------------

    def select_versions(self) -> list:
        """
        Interactive menu to select which content versions to generate.
        Saves tokens by only generating what's needed.
        """
        print("\n" + "=" * 60)
        print("SELECT CONTENT VERSIONS TO GENERATE")
        print("=" * 60)
        print("Which versions do you want? Choose one option:\n")
        print("1) Blog Post only")
        print("2) Social Media Post only")
        print("3) Newsletter only")
        print("4) Blog Post + Social Media")
        print("5) Blog Post + Newsletter")
        print("6) Social Media + Newsletter")
        print("7) All Three (Blog Post + Social Media + Newsletter)")
        print("0) Cancel")

        choice = input("\nEnter number (0-7): ").strip()

        version_map = {
            "1": ["blog_post"],
            "2": ["social_media"],
            "3": ["newsletter"],
            "4": ["blog_post", "social_media"],
            "5": ["blog_post", "newsletter"],
            "6": ["social_media", "newsletter"],
            "7": ["blog_post", "social_media", "newsletter"],
            "0": None,
        }

        selected = version_map.get(choice)
        if selected is None:
            print("[CANCELLED] Generation aborted.")
            return None

        if selected:
            print(f"[OK] Selected: {', '.join([v.replace('_', ' ').title() for v in selected])}")
            return selected

        print("[ERROR] Invalid choice. Please try again.")
        return self.select_versions()

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
        desired_versions: list = None,
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
            desired_versions=desired_versions or ["blog_post", "social_media", "newsletter"],
        )

        print(f"Topic:        {brief.topic}")
        print(f"Format:       {brief.content_type.value}")
        print(f"Template:     {brief.template_type.value}")
        print(f"Key message:  {brief.key_message or '(none specified)'}")
        print(f"Versions:     {', '.join([v.replace('_', ' ').title() for v in brief.desired_versions])}")
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
            desired_versions=brief.desired_versions,
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
    # Stage 4.5: Score
    # ------------------------------------------------------------------

    def stage_score(self, output: ContentOutput) -> ContentScore:
        """
        Evaluate content on 4 dimensions (1-10 each).
        Returns ContentScore with JSON-parsed results.
        """
        print("\n" + "=" * 60)
        print("STAGE 4.5: SCORE (Quality Control)")
        print("=" * 60)

        prompt = self.templates.build_scorer(content=output.generated_text)
        score_json_str = self.llm.generate(prompt)

        try:
            score_data = json.loads(score_json_str)

            score = ContentScore(
                emotional_truth=score_data["emotional_truth"],
                differentiation=score_data["differentiation"],
                brand_integrity=score_data["brand_integrity"],
                authenticity=score_data["authenticity"],
                overall_score=score_data["overall_score"],
                strengths=score_data.get("strengths", []),
                weaknesses=score_data.get("weaknesses", []),
            )

            output.score = score

            print(f"\n[SCORE RESULTS]")
            print(f"  Emotional Truth:    {score.emotional_truth:.1f}/10")
            print(f"  Differentiation:    {score.differentiation:.1f}/10")
            print(f"  Brand Integrity:    {score.brand_integrity:.1f}/10")
            print(f"  Authenticity:       {score.authenticity:.1f}/10")
            print(f"  ──────────────────────")
            print(f"  Overall Score:      {score.overall_score:.1f}/10")

            if score.overall_score >= 8.0:
                print(f"  ✅ THRESHOLD MET (≥8.0) - Ready to stop")
            else:
                print(f"  ⚠️  Below threshold - Iterate further")

            return score

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[ERROR] Scoring failed: {e}")
            print(f"[DEBUG] Response was: {score_json_str[:200]}")
            # Return default low score on error
            return ContentScore(
                emotional_truth=0,
                differentiation=0,
                brand_integrity=0,
                authenticity=0,
                overall_score=0,
                strengths=[],
                weaknesses=["Scoring error"],
            )

    # ------------------------------------------------------------------
    # Stage 4.75: Critique (Multi-Agent Quality Control)
    # ------------------------------------------------------------------

    def stage_critique(self, output: ContentOutput) -> str:
        """
        Ruthlessly evaluate generated content.
        Returns critique feedback as string.
        """
        print("\n" + "=" * 60)
        print("STAGE 4.75: CRITIQUE (Multi-Agent Quality Control)")
        print("=" * 60)

        prompt = self.templates.build_critic(
            content=output.generated_text,
            primary_context=self.primary_context,
            secondary_context=self.secondary_context,
        )

        critique = self.llm.generate(prompt)

        print("\n" + "-" * 60)
        print("CRITIQUE FEEDBACK:")
        print("-" * 60)
        print(critique)
        print("-" * 60)
        print("[OK] Content evaluated.")

        return critique

    # ------------------------------------------------------------------
    # Stage 4.9: Refine (Multi-Agent Improvement)
    # ------------------------------------------------------------------

    def stage_refine_content(self, output: ContentOutput, critique: str) -> ContentOutput:
        """
        Improve content based on critique.
        Returns refined ContentOutput.
        """
        print("\n" + "=" * 60)
        print("STAGE 4.9: REFINE (Multi-Agent Improvement)")
        print("=" * 60)

        prompt = self.templates.build_refiner(
            original_content=output.generated_text,
            critique=critique,
        )

        refined_text = self.llm.generate(prompt)

        # Create new output with refined content
        refined_output = ContentOutput(
            brief=output.brief,
            generated_text=refined_text,
            template_type=output.template_type,
            content_type=output.content_type,
            topic=output.topic,
            iteration=output.iteration,  # Keep original iteration count
        )

        print("\n" + "-" * 60)
        print("REFINED CONTENT:")
        print("-" * 60)
        print(refined_text)
        print("-" * 60)
        print(f"[OK] Content refined. {refined_output.char_count} chars.")

        return refined_output

    # ------------------------------------------------------------------
    # Stage 4.95: Iteration Control Pipeline (with Scoring & Threshold)
    # ------------------------------------------------------------------

    def stage_publish_with_iteration_control(self, brief: ContentBrief, max_loops: int = 1, threshold: float = 8.0) -> ContentOutput:
        """
        Full multi-agent pipeline with iteration:
        Create → Critique → Refine → Score → (loop if score < threshold)

        Args:
            brief: Content brief
            max_loops: Max refinement iterations (default 1 = test version once)
            threshold: Quality threshold to stop (default 8.0/10)

        Returns:
            ContentOutput with highest scoring version
        """
        print("\n" + "=" * 60)
        print(f"MULTI-AGENT ITERATION CONTROL")
        print(f"Max Loops: {max_loops}, Threshold: {threshold:.1f}/10")
        print("=" * 60)

        # LOOP 0: Initial creation
        print("\n[LOOP 0] CREATION")
        output = self.stage_publish(brief)

        best_output = output
        best_score = None

        for loop_num in range(max_loops):
            print(f"\n[LOOP {loop_num + 1}] CRITIQUE → REFINE → SCORE")
            print("-" * 60)

            # Stage 1: Critique
            critique = self.stage_critique(output)

            # Stage 2: Refine
            refined_output = self.stage_refine_content(output, critique)

            # Stage 3: Score
            score = self.stage_score(refined_output)

            # Track best version
            if best_score is None or score.overall_score > best_score.overall_score:
                best_output = refined_output
                best_score = score

            # Decision: Stop if threshold reached
            if score.overall_score >= threshold:
                print(f"\n✅ THRESHOLD MET ({score.overall_score:.1f} ≥ {threshold:.1f})")
                print("Stopping iteration.")
                break
            else:
                print(f"\n⚠️  Below threshold ({score.overall_score:.1f} < {threshold:.1f})")
                if loop_num < max_loops - 1:
                    print("Will iterate further...")
                    output = refined_output
                else:
                    print("Max loops reached. Using best version.")

        # Final: Use best output
        best_output.score = best_score
        self.history[-1] = best_output

        print("\n" + "=" * 60)
        print("ITERATION COMPLETE")
        print(f"Final Score: {best_score.overall_score:.1f}/10")
        print("=" * 60)

        return best_output

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
        Maintains the same content versions as the previous iteration.
        """
        print("\n" + "=" * 60)
        print("STAGE 5: ITERATE")
        print("=" * 60)
        print(f"Feedback: {feedback}")

        refined_brief = ContentBrief(
            topic=previous.brief.topic,
            content_type=previous.brief.content_type,
            template_type=previous.brief.template_type,
            key_message=previous.brief.key_message,
            desired_versions=previous.brief.desired_versions,  # Keep same versions!
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
    # Helper: Parse content versions
    # ------------------------------------------------------------------

    def _parse_content_versions(self, text: str) -> dict:
        """
        Parse generated content to extract individual versions.
        Expected format:
        # BLOG POST VERSION (XXX words)
        [content]
        # SOCIAL MEDIA VERSION (Instagram/Facebook)
        [content]
        # NEWSLETTER VERSION
        [content]
        """
        versions = {}
        lines = text.split('\n')

        current_version = None
        current_content = []

        for line in lines:
            # Check for version headers
            if '# BLOG POST VERSION' in line:
                # Save previous version
                if current_version and current_content:
                    versions[current_version] = '\n'.join(current_content).strip()
                current_version = 'blog_post'
                current_content = []
            elif '# SOCIAL MEDIA VERSION' in line:
                # Save previous version
                if current_version and current_content:
                    versions[current_version] = '\n'.join(current_content).strip()
                current_version = 'social_media'
                current_content = []
            elif '# NEWSLETTER VERSION' in line:
                # Save previous version
                if current_version and current_content:
                    versions[current_version] = '\n'.join(current_content).strip()
                current_version = 'newsletter'
                current_content = []
            else:
                # Collect content for current version
                if current_version:
                    current_content.append(line)

        # Don't forget the last version
        if current_version and current_content:
            versions[current_version] = '\n'.join(current_content).strip()

        # If no versions found, return the whole text as a single version
        if not versions:
            versions['generated_content'] = text.strip()

        return versions

    # ------------------------------------------------------------------
    # HTML Export (CEO-ready presentation output)
    # ------------------------------------------------------------------

    def export_html(
        self,
        output: ContentOutput,
        filepath: str = "output/content_output.html",
        generic_comparison: str = "",
        display_content_type: Optional[str] = None,
    ) -> str:
        """
        Export generated content as a styled HTML file.
        Opens cleanly in any browser – no frameworks, no dependencies.

        Args:
            output:                  ContentOutput from stage_publish() or stage_iterate()
            filepath:                Where to save the HTML file
            generic_comparison:      Optional: paste generic ChatGPT output for side-by-side
            display_content_type:    Optional: which version to display ("social_media", "blog_post", "newsletter")
                                     If None, shows interactive tabs with all available versions
        Returns:
            filepath (str)
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Parse content versions from generated text
        content_versions = self._parse_content_versions(output.generated_text)

        # If display_content_type is specified, show only that version
        # Otherwise, show all available versions with tabs
        if display_content_type and display_content_type in content_versions:
            display_text = content_versions[display_content_type]
            content_block = f"""
    <div class="section">
        <h2>{display_content_type.replace('_', ' ').title()}</h2>
        <div class="content-text">{display_text.replace(chr(10), '<br>')}</div>
    </div>"""
        else:
            # Show all versions with interactive tabs
            tab_buttons = "".join(
                f'<button class="tab-btn" onclick="showTab(\'{version}\')">{version.replace("_", " ").title()}</button>'
                for version in content_versions.keys()
            )
            tab_contents = "".join(
                f'<div id="tab-{version}" class="tab-content" style="display:none;"><div class="content-text">{text.replace(chr(10), "<br>")}</div></div>'
                for version, text in content_versions.items()
            )
            # Show first tab by default
            first_version = next(iter(content_versions.keys()))
            tab_contents = f'<div id="tab-{first_version}" class="tab-content"><div class="content-text">{content_versions[first_version].replace(chr(10), "<br>")}</div></div>' + \
                          "".join(
                f'<div id="tab-{version}" class="tab-content" style="display:none;"><div class="content-text">{text.replace(chr(10), "<br>")}</div></div>'
                for version, text in list(content_versions.items())[1:]
            )

            content_block = f"""
    <div class="section">
        <h2>Generated Content</h2>
        <div class="tabs">
            <div class="tab-buttons">
                {tab_buttons}
            </div>
            {tab_contents}
        </div>
    </div>"""

        # Build comparison block only if generic text is provided
        comparison_block = ""
        if generic_comparison:
            comparison_block = f"""
        <div class="section">
            <h2>⚡ Uniqueness Comparison</h2>
            <div class="comparison-grid">
                <div class="comparison-box our-output">
                    <div class="box-label">Joy of Movement AI System</div>
                    <p>{output.generated_text.replace(chr(10), '<br>')}</p>
                </div>
                <div class="comparison-box generic-output">
                    <div class="box-label">Generic ChatGPT</div>
                    <p>{generic_comparison.replace(chr(10), '<br>')}</p>
                </div>
            </div>
        </div>"""

        # Build KB source tags
        primary_tags = "".join(
            f'<span class="kb-tag primary">📄 {d.filename}</span>'
            for d in self.kb.primary
        )
        secondary_tags = "".join(
            f'<span class="kb-tag secondary">🔍 {d.filename}</span>'
            for d in self.kb.secondary
        )

        feedback_pill = (
            "<div class='pill'><strong>Feedback applied</strong> ✓</div>"
            if output.feedback else ""
        )

        tab_script = """
    <script>
        function showTab(tabName) {
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.style.display = 'none');

            // Remove active class from all buttons
            const buttons = document.querySelectorAll('.tab-btn');
            buttons.forEach(btn => btn.classList.remove('active'));

            // Show selected tab
            const selectedTab = document.getElementById('tab-' + tabName);
            if (selectedTab) selectedTab.style.display = 'block';

            // Add active class to clicked button
            event.target.classList.add('active');
        }

        // Show first tab by default on load
        window.addEventListener('load', function() {
            const firstBtn = document.querySelector('.tab-btn');
            if (firstBtn) firstBtn.classList.add('active');
        });
    </script>
"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Joy of Movement – Content Output</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f4f0;
            color: #1a1a1a;
            padding: 40px 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}

        .header {{
            background: #1a1a1a;
            color: #f5f4f0;
            padding: 32px 40px;
            border-radius: 12px;
            margin-bottom: 24px;
        }}
        .header .brand {{
            font-size: 13px;
            letter-spacing: 2px;
            text-transform: uppercase;
            opacity: 0.6;
            margin-bottom: 8px;
        }}
        .header h1 {{ font-size: 26px; font-weight: 700; margin-bottom: 6px; }}
        .header .subtitle {{ opacity: 0.6; font-size: 14px; }}

        .meta-row {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 24px; }}
        .pill {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 20px;
            padding: 6px 14px;
            font-size: 13px;
            color: #555;
        }}
        .pill strong {{ color: #1a1a1a; }}

        .section {{
            background: white;
            border-radius: 12px;
            padding: 32px 40px;
            margin-bottom: 20px;
            border: 1px solid #e8e8e4;
        }}
        .section h2 {{
            font-size: 11px;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #aaa;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}

        .content-text {{
            font-size: 19px;
            line-height: 1.8;
            color: #1a1a1a;
        }}

        .tabs {{ margin-top: 20px; }}
        .tab-buttons {{
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 0;
        }}
        .tab-btn {{
            background: none;
            border: none;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 600;
            color: #999;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .tab-btn:hover {{
            color: #555;
        }}
        .tab-btn.active {{
            color: #1a1a1a;
            border-bottom-color: #1a1a1a;
        }}
        .tab-content {{
            animation: fadeIn 0.2s;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .kb-tags {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .kb-tag {{
            border-radius: 6px;
            padding: 5px 12px;
            font-size: 13px;
        }}
        .kb-tag.primary {{ background: #e8f4e8; color: #2d6a2d; }}
        .kb-tag.secondary {{ background: #e8eef8; color: #2d4a8a; }}

        .comparison-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .comparison-box {{
            padding: 24px;
            border-radius: 8px;
            font-size: 15px;
            line-height: 1.7;
        }}
        .box-label {{
            font-size: 11px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 14px;
            font-weight: 700;
        }}
        .our-output {{ background: #e8f4e8; border: 1px solid #b8d8b8; }}
        .our-output .box-label {{ color: #2d6a2d; }}
        .generic-output {{ background: #fef9e7; border: 1px solid #d4c97a; }}
        .generic-output .box-label {{ color: #7a6a00; }}

        .footer {{
            text-align: center;
            color: #bbb;
            font-size: 12px;
            margin-top: 32px;
        }}

        @media (max-width: 640px) {{
            .comparison-grid {{ grid-template-columns: 1fr; }}
            .section {{ padding: 24px 20px; }}
            .header {{ padding: 24px 20px; }}
        }}
    </style>
</head>
<body>
<div class="container">

    <div class="header">
        <div class="brand">The Joy of Movement – AI Content System</div>
        <h1>{output.topic}</h1>
        <div class="subtitle">Generated {output.generated_at[:10]} · Iteration {output.iteration}</div>
    </div>

    <div class="meta-row">
        <div class="pill"><strong>Format</strong> {output.content_type}</div>
        <div class="pill"><strong>Template</strong> {output.template_type}</div>
        <div class="pill"><strong>Length</strong> {output.char_count} chars</div>
        {feedback_pill}
    </div>

    {content_block}

    <div class="section">
        <h2>Knowledge Base Sources</h2>
        <div class="kb-tags">
            {primary_tags}
            {secondary_tags}
        </div>
    </div>

    {comparison_block}

    <div class="footer">
        Joy of Movement AI Content Creator · Built with Anthropic Claude
    </div>

</div>
{tab_script}
</body>
</html>"""

        Path(filepath).write_text(html, encoding="utf-8")
        print(f"[OK] HTML exported → {filepath}")
        return filepath

    # ------------------------------------------------------------------
    # Full pipeline (convenience method)
    # ------------------------------------------------------------------

    def run(
        self,
        topic: str,
        content_type: ContentType = ContentType.SOCIAL_MEDIA,
        template_type: TemplateType = TemplateType.HYBRID,
        key_message: str = "",
        desired_versions: list = None,
    ) -> ContentOutput:
        """
        Run the full pipeline in one call.
        Stages: Document → Monitor → Brief → Publish
        (Iterate is manual – call stage_iterate() after reviewing output)

        Args:
            desired_versions: List of versions to generate. If None, ask user interactively.
        """
        self.stage_document()
        self.stage_monitor()

        # Ask user which versions to generate if not specified
        if desired_versions is None:
            desired_versions = self.select_versions()
            if desired_versions is None:
                return None

        brief = self.stage_brief(
            topic=topic,
            content_type=content_type,
            template_type=template_type,
            key_message=key_message,
            desired_versions=desired_versions,
        )
        return self.stage_publish(brief)


# ---------------------------------------------------------------------------
# Note: Use main.py for interactive CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Use: python src/main.py")
    print("This module is meant to be imported, not run directly.")