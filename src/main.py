"""
main.py
=======
CLI entry point for the Joy of Movement AI Content Creator.
Simple pipeline: Document → Monitor → Brief → Publish → Iterate

Usage:
    python src/main.py
"""

import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from content_pipeline import ContentPipeline
from prompt_templates import TemplateType, ContentType

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def print_header():
    print("\n" + "=" * 60)
    print("  THE JOY OF MOVEMENT - AI Content Creator")
    print("  Authentic content for people 55+")
    print("=" * 60)


def save_output(content: str, topic: str, content_type: str) -> str:
    """Save generated content to output/ folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c if c.isalnum() else "_" for c in topic[:30])
    filename = OUTPUT_DIR / f"{timestamp}_{content_type}_{safe_topic}.txt"
    filename.write_text(content, encoding="utf-8")
    return str(filename)


def main():
    print_header()
    print("\nLoading knowledge base...")

    pipeline = ContentPipeline(kb_root="knowledge_base")
    pipeline.stage_document()
    pipeline.stage_monitor()

    while True:
        print("\n" + "=" * 60)
        print("OPTIONS")
        print("=" * 60)
        print("1 -> Generate content")
        print("2 -> Exit")
        choice = input("\nYour choice: ").strip()

        if choice == "1":
            # ===== STAGE 3: BRIEF (nur hier wählen!) =====
            print("\n" + "=" * 60)
            print("STAGE 3: BRIEF")
            print("=" * 60)

            # Topic
            topic = input("Topic (e.g., 'Why community matters after 60'): ").strip()
            if not topic:
                topic = "Why belonging matters more than fitness after 60"

            # Format / Content Type
            print("\nContent format?")
            print("  1 -> Blog Post")
            print("  2 -> Social Media")
            print("  3 -> Newsletter")
            fmt = input("Choose [1/2/3]: ").strip()
            fmt_map = {"1": ContentType.BLOG_POST, "2": ContentType.SOCIAL_MEDIA, "3": ContentType.NEWSLETTER}
            content_type = fmt_map.get(fmt, ContentType.BLOG_POST)
            print(f"✓ Format: {content_type.value}")

            # Template
            print("\nKnowledge base?")
            print("  1 -> Brand only (Primary KB)")
            print("  2 -> Market context only (Secondary KB)")
            print("  3 -> Hybrid - both (recommended)")
            tpl = input("Choose [1/2/3]: ").strip()
            tpl_map = {"1": TemplateType.BRAND, "2": TemplateType.INDUSTRY, "3": TemplateType.HYBRID}
            template_type = tpl_map.get(tpl, TemplateType.HYBRID)
            print(f"✓ Template: {template_type.value}")

            # Key message
            key_message = input("\nKey message (optional, press Enter to skip): ").strip()

            # Notes
            notes = input("Additional notes (optional, press Enter to skip): ").strip()

            print("[OK] Brief created.\n")

            # ===== STAGE 4: PUBLISH =====
            print("=" * 60)
            print("STAGE 4: PUBLISH")
            print("=" * 60)

            output = pipeline.stage_brief(
                topic=topic,
                content_type=content_type,
                template_type=template_type,
                key_message=key_message,
                notes=notes,
            )

            output = pipeline.stage_publish(output)

            if output is None:
                print("[ERROR] Generation failed.")
                continue

            # ===== STAGE 5: ITERATE (optional) =====
            while True:
                print("\nWould you like to refine? (y/n)")
                refine = input().strip().lower()
                if refine == "y":
                    feedback = input("Your feedback: ").strip()
                    output = pipeline.stage_iterate(output, feedback)
                else:
                    break

            # Save
            saved_path = save_output(output.generated_text, topic, content_type.value)
            print(f"[SAVED] → {saved_path}")

            # Export to HTML
            print("\nExport as HTML for presentation? (y/n)")
            if input().strip().lower() == "y":
                html_path = pipeline.export_html(output)
                print(f"[EXPORTED] → {html_path}")

                # Open in browser?
                print("Open in browser? (y/n)")
                if input().strip().lower() == "y":
                    import subprocess
                    subprocess.run(["open", html_path])

        elif choice == "2":
            print("\nBye. Keep moving.\n")
            sys.exit(0)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()