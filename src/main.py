"""
main.py
=======
CLI entry point for the Joy of Movement AI Content Creator.
Interactive menu for demos and daily content generation.

Usage:
    python src/main.py
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add src/ to path so imports work when called from project root
sys.path.insert(0, os.path.dirname(__file__))

from content_pipeline import ContentPipeline
from prompt_templates import TemplateType, ContentType


# ---------------------------------------------------------------------------
# Output directory for saving generated content
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def print_header():
    print("\n" + "=" * 60)
    print("  THE JOY OF MOVEMENT - AI Content Creator")
    print("  Authentic content for people 55+")
    print("=" * 60)


def print_menu():
    print("\nWhat would you like to create?")
    print("  1  -> Social Media Post")
    print("  2  -> Blog Post")
    print("  3  -> Newsletter")
    print("  4  -> Uniqueness comparison (your system vs generic ChatGPT)")
    print("  5  -> Exit")
    print()


def choose_template() -> TemplateType:
    print("Which knowledge base?")
    print("  1 -> Brand only (Primary KB)")
    print("  2 -> Market context only (Secondary KB)")
    print("  3 -> Hybrid - both KBs (recommended for demo)")
    choice = input("Choose [1/2/3]: ").strip()
    mapping = {
        "1": TemplateType.BRAND,
        "2": TemplateType.INDUSTRY,
        "3": TemplateType.HYBRID,
    }
    return mapping.get(choice, TemplateType.HYBRID)


def choose_versions() -> list:
    """Interactive menu to select which content versions to generate."""
    print("\nWhich content versions do you want?")
    print("  1 -> Blog Post only")
    print("  2 -> Social Media Post only")
    print("  3 -> Newsletter only")
    print("  4 -> Blog Post + Social Media")
    print("  5 -> Blog Post + Newsletter")
    print("  6 -> Social Media + Newsletter")
    print("  7 -> All Three (Blog Post + Social Media + Newsletter)")

    choice = input("Choose [1-7]: ").strip()

    version_map = {
        "1": ["blog_post"],
        "2": ["social_media"],
        "3": ["newsletter"],
        "4": ["blog_post", "social_media"],
        "5": ["blog_post", "newsletter"],
        "6": ["social_media", "newsletter"],
        "7": ["blog_post", "social_media", "newsletter"],
    }

    selected = version_map.get(choice, ["blog_post", "social_media", "newsletter"])
    version_names = [v.replace("_", " ").title() for v in selected]
    print(f"✓ Selected: {', '.join(version_names)}")
    return selected


def save_output(content: str, topic: str, content_type: str) -> str:
    """Save generated content to output/ folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c if c.isalnum() else "_" for c in topic[:30])
    filename = OUTPUT_DIR / f"{timestamp}_{content_type}_{safe_topic}.txt"
    filename.write_text(content, encoding="utf-8")
    return str(filename)


def print_uniqueness_note():
    print("\n" + "-" * 60)
    print("WHY THIS OUTPUT IS NOT AI-SLOP:")
    print("-" * 60)
    print("Generic ChatGPT: 'Write a social media post for a")
    print("fitness brand targeting older adults.'")
    print()
    print("Result: 'It's never too late to start your fitness")
    print("journey! Join us and discover the power of movement!'")
    print()
    print("Joy of Movement system does differently:")
    print("  * Reads brand_guidelines.md -> identity-first framing")
    print("  * Reads competitor_analysis.md -> knows what NOT to sound like")
    print("  * Reads market_trends.md -> addresses real 55+ pain points")
    print("  * Template enforces: story first, no motivational cliches")
    print("  * Identity language: 'I am a Mover' not 'I attend classes'")
    print("-" * 60)


# ---------------------------------------------------------------------------
# Content generation flows
# ---------------------------------------------------------------------------

def generate_content(pipeline: ContentPipeline, content_type: ContentType):
    template = choose_template()
    desired_versions = choose_versions()

    topic = input("\nTopic (e.g. 'Starting something new at 60'): ").strip()
    if not topic:
        topic = "Why belonging matters more than fitness after 60"

    key_message = input("Key message (optional, press Enter to skip): ").strip()

    output = pipeline.run(
        topic=topic,
        content_type=content_type,
        template_type=template,
        key_message=key_message,
        desired_versions=desired_versions,
    )

    print("\nWould you like to refine this content? (y/n)")
    if input().strip().lower() == "y":
        feedback = input("Your feedback: ").strip()
        output = pipeline.stage_iterate(output, feedback)

    saved_path = save_output(output.generated_text, topic, content_type.value)
    print(f"\n[SAVED] -> {saved_path}")

    print_uniqueness_note()


def run_comparison(pipeline: ContentPipeline):
    print("\n--- UNIQUENESS COMPARISON ---")
    desired_versions = choose_versions()
    print("\nGenerating Joy of Movement content with full KB context...")

    output = pipeline.run(
        topic="Starting something new at 60",
        content_type=ContentType.SOCIAL_MEDIA,
        template_type=TemplateType.HYBRID,
        key_message="Belonging is the product, movement is the vehicle",
        desired_versions=desired_versions,
    )

    print("\n" + "=" * 60)
    print("JOY OF MOVEMENT OUTPUT (your system):")
    print("=" * 60)
    print(output.generated_text)

    print("\n" + "=" * 60)
    print("GENERIC CHATGPT OUTPUT (for comparison):")
    print("=" * 60)
    print(
        "It's never too late to start your fitness journey!\n"
        "At 60, you have the wisdom, the time, and the opportunity\n"
        "to transform your health. Join our community and discover\n"
        "the power of movement. Your best years are ahead of you!\n"
        "#ActiveAging #FitnessOver60 #HealthyLifestyle #NeverTooLate"
    )

    print("\n" + "=" * 60)
    print("KEY DIFFERENCES:")
    print("=" * 60)
    print("Generic: Motivation-first, performance language, hashtag soup")
    print("JoM:     Story-first, identity language, no cliches, no hashtags")
    print("Generic: 'transform your health' -> fear/deficit framing")
    print("JoM:     'You are a Mover' -> identity/belonging framing")
    print("Generic: Could be written for any brand, any audience")
    print("JoM:     Requires brand_guidelines.md + competitor_analysis.md")
    print("         Structurally unreplicable without context.")

    saved_path = save_output(
        f"JOY OF MOVEMENT:\n{output.generated_text}\n\nGENERIC CHATGPT:\n"
        "It's never too late to start your fitness journey...",
        "uniqueness_comparison",
        "comparison"
    )
    print(f"\n[SAVED] -> {saved_path}")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    print_header()
    print("\nLoading knowledge base...")

    pipeline = ContentPipeline(kb_root="knowledge_base")
    pipeline.stage_document()
    pipeline.stage_monitor()

    while True:
        print_menu()
        choice = input("Your choice: ").strip()

        if choice == "1":
            generate_content(pipeline, ContentType.SOCIAL_MEDIA)
        elif choice == "2":
            generate_content(pipeline, ContentType.BLOG_POST)
        elif choice == "3":
            generate_content(pipeline, ContentType.NEWSLETTER)
        elif choice == "4":
            run_comparison(pipeline)
        elif choice == "5":
            print("\nBye. Keep moving.\n")
            sys.exit(0)
        else:
            print("Invalid choice. Enter 1-5.")


if __name__ == "__main__":
    main()