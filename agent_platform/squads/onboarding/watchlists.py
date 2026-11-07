"""Synthetic Sanctions & Politically Exposed Persons (PEP) Watchlist and Fuzzy Matcher."""

import re
from typing import List
from agent_platform.squads.onboarding.models import ScreeningMatch

# Curated synthetic sanctions & PEP entries for testing and evaluation
WATCHLIST_DATABASE = [
    {
        "name": "Viktor Anatolyevich Petrov",
        "aliases": ["Victor Petrov", "V. Petrov"],
        "list_type": "OFAC_SDN",
        "country": "RU",
        "program": "RUSSIA-EO14024",
    },
    {
        "name": "Carlos Roberto Mendez Gomez",
        "aliases": ["Carlos Mendez", "Roberto Gomez", "El Patron"],
        "list_type": "OFAC_SDN",
        "country": "MX",
        "program": "SDNTK",
    },
    {
        "name": "General Tariq Al-Mansoor",
        "aliases": ["Tariq Mansoor", "Tariq Al Mansour"],
        "list_type": "PEP",
        "country": "SY",
        "program": "SENIOR_MILITARY_OFFICIAL",
    },
    {
        "name": "Elena Rostova",
        "aliases": ["Elena Rostova-Ivanova", "Helena Rostov"],
        "list_type": "EU_SANCTIONS",
        "country": "BY",
        "program": "BELARUS-SANCTIONS",
    },
    {
        "name": "NorthStar Maritime Holdings Ltd",
        "aliases": ["NorthStar Shipping", "NorthStar Marine"],
        "list_type": "OFAC_SDN",
        "country": "CY",
        "program": "MARITIME-EVASION",
    },
]


def normalize_text(text: str) -> str:
    """Normalize string for fuzzy comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    tokens = text.split()
    tokens.sort()
    return " ".join(tokens)


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate character-level Levenshtein edit distance between two strings."""
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    len1, len2 = len(s1), len(s2)
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,      # deletion
                matrix[i][j - 1] + 1,      # insertion
                matrix[i - 1][j - 1] + cost  # substitution
            )

    return matrix[len1][len2]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Calculate character-level Levenshtein similarity ratio (0.0 to 1.0)."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    dist = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return round(1.0 - (dist / max_len), 3)


def screen_name(query_name: str, threshold: float = 0.80) -> List[ScreeningMatch]:
    """Screen an individual or entity name against sanctions and PEP lists using fuzzy matching."""
    matches: List[ScreeningMatch] = []
    norm_query = normalize_text(query_name)

    for entry in WATCHLIST_DATABASE:
        primary_name = entry["name"]
        norm_primary = normalize_text(primary_name)
        score = levenshtein_similarity(norm_query, norm_primary)

        best_score = score
        matched_alias = primary_name

        # Also check aliases
        for alias in entry.get("aliases", []):
            alias_score = levenshtein_similarity(norm_query, normalize_text(alias))
            if alias_score > best_score:
                best_score = alias_score
                matched_alias = alias

        if best_score >= threshold:
            matches.append(
                ScreeningMatch(
                    matched_name=primary_name,
                    searched_query=query_name,
                    list_type=entry["list_type"],
                    match_score=best_score,
                    country=entry.get("country"),
                    program=entry.get("program"),
                    is_exact_match=(best_score == 1.0),
                )
            )

    return matches
