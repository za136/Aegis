"""Onboarding & KYC Agent Squad package."""

from agent_platform.squads.onboarding.agent import OnboardingAgent
from agent_platform.squads.onboarding.extractor import DocumentExtractor, extractor
from agent_platform.squads.onboarding.models import (
    ApplicantType,
    ApplicationStatus,
    DocumentPayload,
    DocumentType,
    ExtractedDocumentData,
    OnboardingApplicationRequest,
    OnboardingDisposition,
    RiskRating,
    ScreeningMatch,
)
from agent_platform.squads.onboarding.watchlists import (
    levenshtein_distance,
    levenshtein_similarity,
    screen_name,
)

__all__ = [
    "OnboardingAgent",
    "DocumentExtractor",
    "extractor",
    "ApplicantType",
    "ApplicationStatus",
    "DocumentPayload",
    "DocumentType",
    "ExtractedDocumentData",
    "OnboardingApplicationRequest",
    "OnboardingDisposition",
    "RiskRating",
    "ScreeningMatch",
    "screen_name",
    "levenshtein_distance",
    "levenshtein_similarity",
]
