"""
llm_integration.py
==================
Handles all communication with the Anthropic Claude API.
Takes a PromptResult, sends it, returns generated content.
"""

import os
from dotenv import load_dotenv
import anthropic

from prompt_templates import PromptResult

load_dotenv()


class LLMIntegration:
    """
    Wraps the Anthropic API.
    Single responsibility: take a PromptResult, return a string.
    """

    MODEL = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 1000

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not found. Check your .env file."
            )
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, prompt: PromptResult) -> str:
        """
        Send a prompt to Claude and return the generated content.

        Args:
            prompt: PromptResult from PromptTemplates.build()

        Returns:
            Generated content as a plain string.
        """
        print(f"\n[LLM] Generating {prompt.content_type} via {prompt.template_type} template...")
        print(f"[LLM] Topic: {prompt.topic}")

        message = self.client.messages.create(
            model=self.MODEL,
            max_tokens=self.MAX_TOKENS,
            system=prompt.system_prompt,
            messages=[
                {"role": "user", "content": prompt.user_prompt}
            ],
        )

        content = message.content[0].text
        print(f"[LLM] Done. {len(content)} chars generated.")
        return content


# ---------------------------------------------------------------------------
# Quick test – generates one real piece of content end-to-end
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from document_processor import DocumentProcessor
    from prompt_templates import PromptTemplates, TemplateType, ContentType

    # 1. Load knowledge base
    processor = DocumentProcessor(kb_root="knowledge_base")
    kb = processor.load_all()
    primary_context = processor.get_context_block(kb.primary, label="PRIMARY KNOWLEDGE BASE")
    secondary_context = processor.get_context_block(kb.secondary, label="SECONDARY RESEARCH")

    # 2. Build prompt
    templates = PromptTemplates()
    prompt = templates.build(
        template_type=TemplateType.HYBRID,
        content_type=ContentType.SOCIAL_MEDIA,
        topic="Starting something new at 60",
        primary_context=primary_context,
        secondary_context=secondary_context,
    )

    # 3. Generate content
    llm = LLMIntegration()
    result = llm.generate(prompt)

    print("\n" + "=" * 60)
    print("GENERATED CONTENT")
    print("=" * 60)
    print(result)
    print("=" * 60)