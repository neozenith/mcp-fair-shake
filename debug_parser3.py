"""Debug subsection extraction for section 3."""

import sys
sys.path.insert(0, '/Users/joshpeak/play/mcp-fair-shake/src')

import re
from mcp_fair_shake.models import Section, Subsection, Paragraph

# Section 3 content from actual parse
content = """(1)  In this Act:
award means:
(a)  a modern award; or
(b)  an enterprise award; or
(c)  a State reference transitional award or Division 2B State reference transitional award.
casual employee means an employee who is employed as a casual employee within the ordinary meaning of that expression.
(2)  A reference in this Act to a person being employed or to employment is a reference to the person being employed, or to employment, under a contract of service."""

# Simulate _extract_subsections logic
section = Section(
    id="/au-federal/fwa/2009/s3",
    title="Definitions",
    content=content,
    act_id="/au-federal/fwa/2009",
    section_number="3",
)

lines = content.split("\n")
current_subsection = None
current_paragraph = None
content_lines = []
registry = {}

print(f"Processing {len(lines)} lines...")

for i, line in enumerate(lines):
    line_orig = line
    line = line.strip()
    if not line:
        continue

    print(f"\n[{i}] Line: '{line[:60]}...' " if len(line) > 60 else f"\n[{i}] Line: '{line}'")

    # Subsection marker
    subsec_match = re.match(r"^\((\d+[a-z]*)\)\s+(.+)$", line)
    if subsec_match:
        print(f"  ✓ SUBSECTION MATCH: {subsec_match.groups()}")

        # Save previous paragraph content
        if current_paragraph and content_lines:
            print(f"    Saving content to paragraph {current_paragraph.id}")
            current_paragraph.content += " " + " ".join(content_lines)
            content_lines = []
        # Save previous subsection content
        elif current_subsection and content_lines:
            print(f"    Saving content to subsection {current_subsection.id}")
            current_subsection.content += " " + " ".join(content_lines)
            content_lines = []

        subsec_number, subsec_content = subsec_match.groups()
        subsec_id = f"{section.id}/{subsec_number}"

        current_subsection = Subsection(
            id=subsec_id,
            title="",
            content=subsec_content,
            section_id=section.id,
            subsection_number=subsec_number,
            parent_id=section.id,
        )
        registry[subsec_id] = current_subsection
        section.subsections.append(subsec_id)
        section.children_ids.append(subsec_id)
        print(f"    Created subsection: {subsec_id}")
        print(f"    Section.subsections = {section.subsections}")
        current_paragraph = None
        continue

    # Paragraph marker
    para_match = re.match(r"^\(([a-z]+)\)\s+(.+)$", line)
    if para_match:
        print(f"  ✓ PARAGRAPH MATCH: {para_match.groups()}")

        # Save collected content
        if current_paragraph and content_lines:
            print(f"    Saving content to paragraph {current_paragraph.id}")
            current_paragraph.content += " " + " ".join(content_lines)
            content_lines = []
        elif current_subsection and content_lines:
            print(f"    Saving content to subsection {current_subsection.id}")
            current_subsection.content += " " + " ".join(content_lines)
            content_lines = []

        para_letter, para_content = para_match.groups()

        # Determine parent
        if current_subsection:
            para_id = f"{current_subsection.id}/{para_letter}"
            parent_id = current_subsection.id
        else:
            para_id = f"{section.id}/{para_letter}"
            parent_id = section.id

        current_paragraph = Paragraph(
            id=para_id,
            title="",
            content=para_content,
            subsection_id=current_subsection.id if current_subsection else None,
            paragraph_letter=para_letter,
            parent_id=parent_id,
        )
        registry[para_id] = current_paragraph

        if current_subsection:
            current_subsection.paragraphs.append(para_id)
            current_subsection.children_ids.append(para_id)
            print(f"    Created paragraph: {para_id} under subsection {current_subsection.id}")
        else:
            section.children_ids.append(para_id)
            print(f"    Created paragraph: {para_id} under section {section.id}")

        continue

    # Collect content
    print(f"  → Collecting content line")
    content_lines.append(line)

# Save last item
if current_paragraph and content_lines:
    print(f"\nFinal: Saving content to paragraph {current_paragraph.id}")
    current_paragraph.content += " " + " ".join(content_lines)
elif current_subsection and content_lines:
    print(f"\nFinal: Saving content to subsection {current_subsection.id}")
    current_subsection.content += " " + " ".join(content_lines)

print(f"\n\nFINAL RESULTS:")
print(f"Section subsections: {section.subsections}")
print(f"Section children_ids: {section.children_ids}")
print(f"Registry entries: {sorted(registry.keys())}")
