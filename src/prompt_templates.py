"""
prompt_templates.py
===================
Reusable prompt templates for Joy of Movement content generation.
Three templates, each with a distinct purpose and knowledge base focus.

Template 1: Brand-Aligned Content     → uses Primary KB
Template 2: Industry-Contextual       → uses Secondary KB
Template 3: Hybrid (Full Context)     → uses both KBs
"""

from dataclasses import dataclass
from enum import Enum


class ContentType(Enum):
    BLOG_POST = "blog_post"
    SOCIAL_MEDIA = "social_media"
    NEWSLETTER = "newsletter"


class TemplateType(Enum):
    BRAND = "brand"
    INDUSTRY = "industry"
    HYBRID = "hybrid"


@dataclass
class PromptResult:
    """Holds a fully assembled prompt ready for the LLM."""
    system_prompt: str
    user_prompt: str
    template_type: str
    content_type: str
    topic: str


# ---------------------------------------------------------------------------
# Base system prompt – shared across all templates
# ---------------------------------------------------------------------------

BASE_SYSTEM = """You are the content voice of "The Joy of Movement" — a German community brand
for people 55+. You do not work for a fitness studio. You build identity and belonging.

ALWAYS:
- Write in English unless instructed otherwise
- Use "you" not "Sie" — warm, direct, eye-level
- Lead with images and stories before facts
- Write short sentences with weight
- Use identity language: "you are a Mover", not "you attend our classes"

NEVER:
- Use "seniors", "anti-aging", "optimize", "train harder", "journey", "embrace", "best years", "incredible benefits"
- Write medical or clinical framing
- Use generic motivational phrases ("unleash your potential", "transform yourself", "live your best life")
- Reference competitors by name
- Sound like a fitness brand or a healthcare provider
- Use call-to-action language ("Join us!", "Start today!", "Sign up now!")
- Write about "staying young" or "fighting age"

The brand voice: warm and direct. Like a trusted friend who happens to know
exactly what this life stage feels like — and isn't afraid to say it out loud."""


# ---------------------------------------------------------------------------
# Template 1: Brand-Aligned Content
# Uses Primary Knowledge Base only
# ---------------------------------------------------------------------------

TEMPLATE_1_SYSTEM = BASE_SYSTEM + """

You have been given the company's Primary Knowledge Base below.
Use it to ensure every piece of content reflects:
- Correct brand voice and tone
- Accurate product descriptions and membership tiers
- Real rituals, symbols, and membership language
- The North Star: "I don't go to a class. I am a Mover."
"""

TEMPLATE_1_USER = """PRIMARY KNOWLEDGE BASE:
{primary_context}

---

TASK:
Create {versions} about: {topic}

Content requirements:
- Open with a real person's story or a concrete moment (not a statistic)
- Reflect the brand identity: movement as vehicle, belonging as product
- Include at least one identity statement (what the reader IS, not what they DO)
- End with a clear, warm invitation — not a sales call to action
- Tone: warm, direct, confident — never pleading or performative

Length guidelines:
- Blog post: 300–450 words
- Social media: 80–120 words
- Newsletter: 200–300 words

{version_instructions}

Output only the final content. No meta-commentary."""


# ---------------------------------------------------------------------------
# Template 2: Industry-Contextual Content
# Uses Secondary Research Layer only
# ---------------------------------------------------------------------------

TEMPLATE_2_SYSTEM = BASE_SYSTEM + """

You have been given the Secondary Research Layer below — market trends,
competitor analysis, and industry context for the German 55+ movement market.
Use this to position content that:
- Speaks to real market dynamics without sounding like a market report
- Differentiates Joy of Movement from generic competitors (Sportverein, VHS,
  commercial studios) through implication, not direct comparison
- Addresses real pain points of the 55+ audience based on market evidence
- Reflects current cultural shifts in how this demographic sees itself
"""

TEMPLATE_2_USER = """SECONDARY RESEARCH LAYER:
{secondary_context}

---

TASK:
Create {versions} about: {topic}

Content requirements:
- Ground the content in real market insight (without quoting statistics)
- Address an unmet need in the 55+ German market
- Position Joy of Movement as the obvious answer — through story, not argument
- Avoid naming competitors; imply the contrast
- Tone: confident, culturally aware, slightly provocative

Length guidelines:
- Blog post: 300–450 words
- Social media: 80–120 words
- Newsletter: 200–300 words

{version_instructions}

Output only the final content. No meta-commentary."""


# ---------------------------------------------------------------------------
# Template 3: Hybrid Content (Full Context)
# Uses both knowledge bases — maximum differentiation
# ---------------------------------------------------------------------------

TEMPLATE_3_SYSTEM = BASE_SYSTEM + """

You have been given both knowledge bases:
- Primary: Joy of Movement brand, products, voice, rituals
- Secondary: German market context, competitor landscape, 55+ trends

This is the highest-fidelity template. Use it to create content that:
- Is unmistakably Joy of Movement (brand voice, identity language)
- Is grounded in real market context (competitor gaps, cultural moment)
- Cannot be replicated by generic ChatGPT — because it requires knowing
  both the brand and the market simultaneously
- Demonstrates clear differentiation: this is what "AI-Slop" cannot produce
"""

TEMPLATE_3_USER = """PRIMARY KNOWLEDGE BASE:
{primary_context}

---

SECONDARY RESEARCH LAYER:
{secondary_context}

---

TASK:
Create {versions} about: {topic}

Content requirements:
- Open with a specific, human moment — not a brand statement
- Weave in one market insight naturally (cultural shift, unmet need)
- Use at least one brand ritual or identity element (membership language,
  the North Star, the opening ritual concept)
- Show — don't tell — why Joy of Movement is different
- Close with identity reinforcement: who the reader becomes, not what they get
- Tone: warm, direct, confident, slightly literary

Length guidelines:
- Blog post: 350–500 words
- Social media: 90–130 words
- Newsletter: 250–350 words

{version_instructions}

Output only the final content(s). No meta-commentary."""


# ---------------------------------------------------------------------------
# Template 4: Scoring Auditor
# Evaluates content quality against brand criteria
# ---------------------------------------------------------------------------

SCORING_SYSTEM = """You are a brand voice auditor for "The Joy of Movement".
Your job: evaluate generated content against these EXACT brand criteria.

VOICE AUTHENTICITY (1-10):
- Does it sound like a trusted friend, not a fitness brand?
- Warm, direct, eye-level tone? Not corporate or clinical?
- Stories before facts?
- Short sentences with weight?

CONSTRAINT COMPLIANCE (1-10):
- No forbidden words: seniors, anti-aging, optimize, train harder, journey,
  embrace, best years, incredible benefits, "staying young", "fighting age"
- No generic CTAs: Join us!, Start today!, Sign up now!
- No medical framing, no patronizing tone
- No generic motivational phrases

IDENTITY CLARITY (1-10):
- Contains explicit identity statements ("You are a...", "This is who you are...")
- Uses member language: "Mover" not "participant"?
- Reinforces North Star: "I am Joy of Movement"?

STORY QUALITY (1-10):
- Opens with real person/concrete moment (not a statistic)?
- Has emotional resonance?
- Feels authentic, not manufactured?

COMPETITOR CONTRAST (1-10):
- Differentiates from Sportverein, VHS, commercial studios?
- Shows gaps they miss (through implication, not direct comparison)?
- Positions Joy of Movement as obvious solution?

Return ONLY valid JSON (no markdown, no explanation):"""

SCORING_USER = """Evaluate this content:

{content}

Return JSON (only, no other text):
{{
  "voice_authenticity": 8,
  "constraint_compliance": 9,
  "identity_clarity": 7,
  "story_quality": 8,
  "competitor_contrast": 6,
  "overall_score": 7.6,
  "feedback": "Strong voice and identity messaging...",
  "issues": [
    {{
      "problem": "Uses forbidden word 'journey'",
      "suggestion": "Replace with 'path', 'chapter', or 'story'"
    }}
  ]
}}"""


# ---------------------------------------------------------------------------
# Template assembler
# ---------------------------------------------------------------------------

class PromptTemplates:
    """
    Assembles fully formed prompts by injecting knowledge base context
    and content parameters into the correct template.
    """

    def _build_version_instructions(self, desired_versions: list) -> str:
        """
        Build specific instructions for which versions to generate.
        """
        if len(desired_versions) == 1:
            version_name = desired_versions[0].replace("_", " ").title()
            return f"Generate ONLY a {version_name} version."
        else:
            version_names = [v.replace("_", " ").title() for v in desired_versions]
            versions_str = " + ".join(version_names)
            return f"Generate all three versions: {versions_str}.\nLabel each section clearly with its type."

    def build(
        self,
        template_type: TemplateType,
        content_type: ContentType,
        topic: str,
        primary_context: str = "",
        secondary_context: str = "",
        desired_versions: list = None,
    ) -> PromptResult:
        """
        Build a complete prompt ready for the LLM.

        Args:
            template_type:      Which template to use (BRAND/INDUSTRY/HYBRID)
            content_type:       Output format (BLOG_POST/SOCIAL_MEDIA/NEWSLETTER)
            topic:              What to write about
            primary_context:    Primary KB text (from DocumentProcessor)
            secondary_context:  Secondary KB text (from DocumentProcessor)
            desired_versions:   List of versions to generate (["blog_post", "social_media", "newsletter"])
                               If None, generates all three

        Returns:
            PromptResult with system_prompt and user_prompt ready to send.
        """
        if desired_versions is None:
            desired_versions = ["blog_post", "social_media", "newsletter"]

        ct_label = content_type.value.replace("_", " ")

        # Build version instructions for the prompt
        version_instructions = self._build_version_instructions(desired_versions)

        # Build version label for prompt
        if len(desired_versions) == 1:
            versions_label = f"a {desired_versions[0].replace('_', ' ')}"
        else:
            version_names = [v.replace("_", " ") for v in desired_versions]
            versions_label = " + ".join(version_names)

        if template_type == TemplateType.BRAND:
            system = TEMPLATE_1_SYSTEM
            user = TEMPLATE_1_USER.format(
                primary_context=primary_context or "[No primary context loaded]",
                versions=versions_label,
                version_instructions=version_instructions,
                topic=topic,
            )

        elif template_type == TemplateType.INDUSTRY:
            system = TEMPLATE_2_SYSTEM
            user = TEMPLATE_2_USER.format(
                secondary_context=secondary_context or "[No secondary context loaded]",
                versions=versions_label,
                version_instructions=version_instructions,
                topic=topic,
            )

        elif template_type == TemplateType.HYBRID:
            system = TEMPLATE_3_SYSTEM
            user = TEMPLATE_3_USER.format(
                primary_context=primary_context or "[No primary context loaded]",
                secondary_context=secondary_context or "[No secondary context loaded]",
                versions=versions_label,
                version_instructions=version_instructions,
                topic=topic,
            )

        else:
            raise ValueError(f"Unknown template type: {template_type}")

        return PromptResult(
            system_prompt=system,
            user_prompt=user,
            template_type=template_type.value,
            content_type=content_type.value,
            topic=topic,
        )

    def list_templates(self) -> None:
        """Print available templates and their use cases."""
        print("\n=== AVAILABLE PROMPT TEMPLATES ===")
        print("BRAND   → Primary KB only. Brand voice, identity, rituals.")
        print("INDUSTRY → Secondary KB only. Market positioning, competitor contrast.")
        print("HYBRID  → Both KBs. Maximum differentiation. Use for demos.")
        print("\nContent types: blog_post | social_media | newsletter")


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    templates = PromptTemplates()
    templates.list_templates()

    # Test: assemble a hybrid prompt
    result = templates.build(
        template_type=TemplateType.HYBRID,
        content_type=ContentType.SOCIAL_MEDIA,
        topic="Starting something new at 60",
        primary_context="[PRIMARY KB PLACEHOLDER]",
        secondary_context="[SECONDARY KB PLACEHOLDER]",
    )

    print(f"\n--- PROMPT ASSEMBLED ---")
    print(f"Template: {result.template_type}")
    print(f"Content type: {result.content_type}")
    print(f"Topic: {result.topic}")
    print(f"\nSystem prompt (first 200 chars):\n{result.system_prompt[:200]}...")
    print(f"\nUser prompt (first 300 chars):\n{result.user_prompt[:300]}...")