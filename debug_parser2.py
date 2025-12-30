"""Debug parser directly."""

import sys
sys.path.insert(0, '/Users/joshpeak/play/mcp-fair-shake/src')

from pathlib import Path
from mcp_fair_shake.parsers.federal_text import FederalTextParser

# Load fixture
fixture_path = Path("/Users/joshpeak/play/mcp-fair-shake/tests/fixtures/fwa-2009-sample.txt")
content = fixture_path.read_bytes()

# Parse
parser = FederalTextParser()
metadata = {
    "canonical_id": "/au-federal/fwa/2009",
    "jurisdiction": "au-federal",
    "year": 2009,
    "title": "Fair Work Act 2009",
}

act, registry = parser.parse(content, metadata)

# Check section 3
section_3_id = "/au-federal/fwa/2009/s3"
if section_3_id in registry:
    section_3 = registry[section_3_id]
    print(f"Section 3 ID: {section_3.id}")
    print(f"Section 3 title: {section_3.title}")
    print(f"Section 3 content length: {len(section_3.content)}")
    print(f"Section 3 subsections: {section_3.subsections}")
    print(f"Section 3 children_ids: {section_3.children_ids}")
    print(f"\nFirst 200 chars of content:")
    print(section_3.content[:200])
else:
    print(f"Section 3 not found!")

print(f"\nTotal registry entries: {len(registry)}")
print("Registry keys:")
for key in sorted(registry.keys()):
    print(f"  {key}")
