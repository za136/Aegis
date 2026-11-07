"""Anti-Money Laundering (AML) Policy Knowledge Corpus & Retrieval Engine."""

import math
import re
from typing import Dict, List
from agent_platform.squads.aegis.models import PolicyExcerpt

# Curated AML Policy Manual and Regulatory Guidance Corpus
POLICY_CORPUS = [
    {
        "excerpt_id": "POL-CTR-5324",
        "policy_name": "Bank Secrecy Act - Anti-Structuring Provisions",
        "section": "31 U.S.C. § 5324 / 31 CFR § 1010.314",
        "citation": "FinCEN Currency Transaction Reporting (CTR) Structuring Prohibitions",
        "content": (
            "No person shall, for the purpose of evading the reporting requirements of 31 U.S.C. 5313(a), "
            "structure or assist in structuring any transaction with one or more domestic financial institutions. "
            "Structuring occurs when an individual or entity conducts multiple cash or wire transfers in amounts "
            "strictly below the $10,000 threshold (e.g., repeated transactions of $9,000 to $9,950) within a short "
            "time window (typically 24 to 72 hours), followed by consolidation or offshore transfer."
        ),
        "keywords": ["structuring", "smurfing", "threshold", "10,000", "5324", "ctr", "fincen", "evasion", "multiple"],
    },
    {
        "excerpt_id": "POL-RAPID-002",
        "policy_name": "FATF Guidance on Wire Transfers & Rapid Movement",
        "section": "FATF Recommendation 16 / Meridian AML-POL-02",
        "citation": "In-and-Out Rapid Movement and Pass-Through Account Behaviour",
        "content": (
            "Accounts that receive large incoming deposits immediately followed by rapid outward dispatches "
            "(within less than 2 to 4 hours) with minimal or near-zero ending balance retention exhibit classic "
            "conduit or mule characteristics. Financial institutions must identify the ultimate economic rationale "
            "for such rapid pass-through activity."
        ),
        "keywords": ["rapid", "movement", "pass-through", "conduit", "mule", "latency", "outflow", "hours", "retention"],
    },
    {
        "excerpt_id": "POL-LAYER-003",
        "policy_name": "Meridian Bank Financial Crime Prevention Policy",
        "section": "Meridian Policy Manual AML-POL-03 (Layering & Shell Entities)",
        "citation": "Multi-Hop Layering and Intermediate Shell Routing",
        "content": (
            "Layering involves the deliberate movement of funds across multiple accounts or corporate entities "
            "with no obvious commercial justification, designed to obfuscate the audit trail between the source "
            "and final destination. Indicators include shell companies registered in high-risk jurisdictions, "
            "round-tripping, and transfers where funds dwell for under 24 hours."
        ),
        "keywords": ["layering", "shell", "hops", "intermediate", "jurisdiction", "round-tripping", "obfuscate"],
    },
    {
        "excerpt_id": "POL-SAR-004",
        "policy_name": "FFIEC BSA/AML Examination Manual - SAR Reporting",
        "section": "31 CFR § 1020.320 / Meridian Case Narrative Standards",
        "citation": "Mandatory Suspicious Activity Report (SAR) Filing Standards",
        "content": (
            "A financial institution must file a SAR for any transaction conducted or attempted by, at, or through "
            "the bank involving $5,000 or more if the bank knows, suspects, or has reason to suspect that the funds "
            "involve illegal activity or are designed to evade BSA requirements. The narrative must clearly articulate "
            "the five essential elements of suspicious activity: Who, What, When, Where, and Why, and must reference "
            "verifiable transaction evidence."
        ),
        "keywords": ["sar", "suspicious", "filing", "narrative", "evidence", "ffiec", "1020.320", "5,000"],
    },
]


def _tokenize(text: str) -> List[str]:
    """Tokenize and normalize text."""
    return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 2]


def retrieve_policies(query: str, top_k: int = 3) -> List[PolicyExcerpt]:
    """Retrieve policy excerpts relevant to the query using semantic keyword overlap and TF scoring."""
    query_tokens = _tokenize(query)
    scores: List[tuple[float, Dict]] = []

    for item in POLICY_CORPUS:
        score = 0.0
        content_tokens = _tokenize(item["content"])
        keywords = item["keywords"]

        # Exact and keyword matches
        for q in query_tokens:
            if q in keywords:
                score += 3.0
            if q in content_tokens:
                score += 1.0

        # Length normalization
        norm_score = round(score / math.sqrt(len(content_tokens) + 1), 3)
        scores.append((norm_score, item))

    # Sort descending
    scores.sort(key=lambda x: x[0], reverse=True)

    results: List[PolicyExcerpt] = []
    for norm_score, item in scores[:top_k]:
        results.append(
            PolicyExcerpt(
                excerpt_id=item["excerpt_id"],
                policy_name=item["policy_name"],
                section=item["section"],
                citation=item["citation"],
                content=item["content"],
                relevance_score=max(norm_score, 0.5),
            )
        )

    return results
