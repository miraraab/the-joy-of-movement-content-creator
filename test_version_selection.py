#!/usr/bin/env python
"""
Test script for version selection feature.
Demonstrates generating only specific content versions.
"""

from src.content_pipeline import ContentPipeline
from src.prompt_templates import ContentType, TemplateType

def test_blog_post_only():
    """Test: Generate Blog Post only"""
    print("\n" + "="*60)
    print("TEST 1: BLOG POST ONLY")
    print("="*60)

    pipeline = ContentPipeline(kb_root='knowledge_base')
    output = pipeline.run(
        topic="Why community matters more than fitness after 60",
        content_type=ContentType.SOCIAL_MEDIA,
        template_type=TemplateType.HYBRID,
        key_message="Belonging is the product, movement is the vehicle",
        desired_versions=['blog_post']
    )

    if output:
        print(f"✅ Generated {output.char_count} chars")
        print(f"   Versions requested: {output.brief.desired_versions}")
        return True
    return False

def test_social_media_only():
    """Test: Generate Social Media only"""
    print("\n" + "="*60)
    print("TEST 2: SOCIAL MEDIA ONLY")
    print("="*60)

    pipeline = ContentPipeline(kb_root='knowledge_base')
    output = pipeline.run(
        topic="Why community matters more than fitness after 60",
        content_type=ContentType.SOCIAL_MEDIA,
        template_type=TemplateType.HYBRID,
        key_message="Belonging is the product, movement is the vehicle",
        desired_versions=['social_media']
    )

    if output:
        print(f"✅ Generated {output.char_count} chars")
        print(f"   Versions requested: {output.brief.desired_versions}")
        return True
    return False

def test_all_three():
    """Test: Generate all three versions"""
    print("\n" + "="*60)
    print("TEST 3: ALL THREE VERSIONS")
    print("="*60)

    pipeline = ContentPipeline(kb_root='knowledge_base')
    output = pipeline.run(
        topic="Why community matters more than fitness after 60",
        content_type=ContentType.SOCIAL_MEDIA,
        template_type=TemplateType.HYBRID,
        key_message="Belonging is the product, movement is the vehicle",
        desired_versions=['blog_post', 'social_media', 'newsletter']
    )

    if output:
        print(f"✅ Generated {output.char_count} chars")
        print(f"   Versions requested: {output.brief.desired_versions}")
        return True
    return False

if __name__ == "__main__":
    print("\n🧪 Testing Version Selection Feature")
    print("="*60)

    results = []
    results.append(("Blog Post Only", test_blog_post_only()))
    results.append(("Social Media Only", test_social_media_only()))
    results.append(("All Three", test_all_three()))

    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    total_passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
