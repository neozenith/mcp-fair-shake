"""Plain language summaries for Australian legislation.

This module provides non-lawyer friendly explanations of key sections
from Australian workplace legislation.
"""

# Summaries database: canonical_id -> {section -> summary}
SUMMARIES: dict[str, dict[str, str]] = {
    "/au-federal/fwa/2009": {
        "general": """
The Fair Work Act 2009 is Australia's main workplace relations law. It sets out:
- Employee rights and employer obligations
- Rules about unfair dismissal and general protections
- How workplace agreements are made
- The Fair Work Commission's powers
- Modern Awards (minimum employment conditions)
        """.strip(),
        "s385": """
**What is unfair dismissal?**

A dismissal is unfair if:
1. You were dismissed from your job
2. The dismissal was harsh, unjust or unreasonable
3. It wasn't a genuine redundancy

This section defines when you can make an unfair dismissal claim to the Fair Work Commission.
        """.strip(),
        "s394": """
**Unfair dismissal remedies**

If the Fair Work Commission finds your dismissal was unfair, they can order:
1. **Reinstatement**: Get your job back with back pay
2. **Compensation**: Money payment (up to 6 months' pay)

The Commission decides which remedy is appropriate based on your circumstances.
        """.strip(),
    },
    "/au-victoria/ohs/2004": {
        "general": """
The Occupational Health and Safety Act 2004 (Vic) protects worker health and safety.

Key points:
- Employers must provide a safe workplace
- Workers have the right to refuse unsafe work
- Everyone has duties to maintain workplace safety
- WorkSafe Victoria enforces the law
        """.strip(),
        "s21": """
**Employer's duty of care**

Your employer must:
1. Provide a safe workplace
2. Provide safe equipment and systems
3. Provide information, instruction, training and supervision
4. Monitor your health and workplace conditions
5. Maintain safe facilities (toilets, drinking water, etc.)

This is the main duty employers owe to employees for workplace safety.
        """.strip(),
        "s23": """
**Worker's safety duties**

As a worker, you must:
1. Take reasonable care for your own safety
2. Take reasonable care not to endanger others
3. Cooperate with your employer on safety matters
4. Not intentionally interfere with safety equipment

These are your responsibilities to help maintain a safe workplace.
        """.strip(),
    },
    "/au-victoria/eoa/2010": {
        "general": """
The Equal Opportunity Act 2010 (Vic) protects you from discrimination, sexual harassment
and victimization.

Protected attributes include:
- Age, disability, gender identity, race, religion
- Political belief, pregnancy, sexual orientation
- And many others

You can make a complaint to the Victorian Equal Opportunity and Human Rights Commission.
        """.strip(),
        "s7": """
**What is discrimination?**

Direct discrimination is when you're treated unfavorably because of a protected attribute
(like your age, race, gender, disability, etc.).

Indirect discrimination is when a rule or policy seems neutral but unfairly disadvantages
people with a protected attribute.
        """.strip(),
    },
    "/au-victoria/lsl/2018": {
        "general": """
The Long Service Leave Act 2018 (Vic) gives you the right to paid long service leave
after working for the same employer for a long time.

Key points:
- You're entitled after 7 years of continuous service
- You can take pro-rata leave from 7 years onwards
- The leave helps recognize long-term employment
- Rates and entitlements depend on your employment type
        """.strip(),
    },
    "/au-victoria/wca/1958": {
        "general": """
The Workers Compensation Act 1958 (Vic) provides compensation if you're injured at work.

Key points:
- Medical expenses covered
- Weekly payments if you can't work
- Lump sum payments for permanent impairment
- Covers most workplace injuries and diseases
- Managed through WorkSafe Victoria
        """.strip(),
    },
    "/au-victoria/aca/1985": {
        "general": """
The Accident Compensation Act 1985 (Vic) is the main workers' compensation law in Victoria.

It provides:
- Medical and hospital treatment
- Income support while you can't work
- Rehabilitation services
- Compensation for permanent injuries
- Death benefits for families

This Act works alongside the Workers Compensation Act 1958.
        """.strip(),
    },
}


def get_summary(canonical_id: str, section: str | None = None) -> str | None:
    """Get a plain language summary for legislation.

    Args:
        canonical_id: Canonical legislation ID
        section: Optional section (e.g., "s21")

    Returns:
        Plain language summary, or None if not available
    """
    # Get summaries for this legislation
    leg_summaries = SUMMARIES.get(canonical_id, {})

    if section:
        # Try to find section-specific summary
        return leg_summaries.get(section) or leg_summaries.get("general")
    else:
        # Return general summary
        return leg_summaries.get("general")


def list_available_summaries() -> dict[str, list[str]]:
    """List all available summaries.

    Returns:
        Dict mapping canonical IDs to lists of sections with summaries
    """
    result = {}
    for canonical_id, sections in SUMMARIES.items():
        result[canonical_id] = list(sections.keys())
    return result
