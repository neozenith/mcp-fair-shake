"""Debug script for parser."""

import re

content = """(1)  In this Act:
award means:
(a)  a modern award; or
(b)  an enterprise award; or
(c)  a State reference transitional award or Division 2B State reference transitional award.
casual employee means an employee who is employed as a casual employee within the ordinary meaning of that expression.
(2)  A reference in this Act to a person being employed or to employment is a reference to the person being employed, or to employment, under a contract of service."""

lines = content.split("\n")

for i, line in enumerate(lines):
    line = line.strip()
    print(f"{i}: '{line}'")

    subsec_match = re.match(r"^\((\d+[a-z]*)\)\s+(.+)$", line)
    if subsec_match:
        print(f"  -> SUBSECTION MATCH: {subsec_match.groups()}")

    para_match = re.match(r"^\(([a-z]+)\)\s+(.+)$", line)
    if para_match:
        print(f"  -> PARAGRAPH MATCH: {para_match.groups()}")
