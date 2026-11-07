"""Unit and Integration Tests for Onboarding & KYC Agent Squad."""

import pytest
from agent_platform.gateway.approvals import approval_inbox
from agent_platform.gateway.models import TicketStatus
from agent_platform.squads.onboarding.agent import OnboardingAgent
from agent_platform.squads.onboarding.extractor import extractor
from agent_platform.squads.onboarding.models import (
    ApplicantType,
    ApplicationStatus,
    DocumentPayload,
    DocumentType,
    OnboardingApplicationRequest,
    RiskRating,
)
from agent_platform.squads.onboarding.watchlists import (
    levenshtein_distance,
    levenshtein_similarity,
    screen_name,
)
import agent_platform.squads.onboarding.tools  # Register tools in gateway


def test_levenshtein_distance_and_similarity():
    """Verify Levenshtein distance and similarity ratio calculations."""
    assert levenshtein_distance("", "") == 0
    assert levenshtein_distance("kitten", "sitting") == 3
    assert levenshtein_distance("rosettacode", "raisethysword") == 8
    assert levenshtein_distance("same", "same") == 0

    assert levenshtein_similarity("same", "same") == 1.0
    assert levenshtein_similarity("", "abc") == 0.0
    assert levenshtein_similarity("kitten", "sitting") == round(1.0 - (3 / 7), 3)


def test_fuzzy_watchlist_screening():
    """Verify fuzzy sanctions and PEP matching across exact names, aliases, and transliterations."""
    # Exact match on OFAC SDN
    hits_exact = screen_name("Viktor Anatolyevich Petrov", threshold=0.85)
    assert len(hits_exact) > 0
    assert hits_exact[0].list_type == "OFAC_SDN"
    assert hits_exact[0].is_exact_match is True

    # Alias / Transliteration match
    hits_alias = screen_name("Victor Petrov", threshold=0.80)
    assert len(hits_alias) > 0
    assert "Petrov" in hits_alias[0].matched_name

    # PEP Match
    hits_pep = screen_name("Tariq Al-Mansour", threshold=0.80)
    assert len(hits_pep) > 0
    assert hits_pep[0].list_type == "PEP"

    # Clean benign name
    clean_hits = screen_name("Alice Elizabeth Smith", threshold=0.80)
    assert len(clean_hits) == 0


def test_document_extractor_defects():
    """Verify defect detection for expired IDs, name mismatches, and tampered documents."""
    # 1. Clean valid document
    valid_doc = DocumentPayload(
        doc_type=DocumentType.PASSPORT,
        document_number="P987654321",
        raw_content="United States Passport: Alice Smith DOB: 1990-05-15",
        expiry_date="2030-01-01",
        holder_name="Alice Smith",
    )
    res_valid = extractor.extract_and_verify(valid_doc, declared_name="Alice Smith")
    assert res_valid.defect_detected is False
    assert res_valid.is_expired is False

    # 2. Expired document
    expired_doc = DocumentPayload(
        doc_type=DocumentType.DRIVERS_LICENSE,
        document_number="DL12345678",
        raw_content="Drivers License: Bob Vance DOB: 1985-02-10",
        expiry_date="2020-01-01",  # Past
        holder_name="Bob Vance",
    )
    res_expired = extractor.extract_and_verify(expired_doc, declared_name="Bob Vance")
    assert res_expired.defect_detected is True
    assert res_expired.is_expired is True
    assert "expired" in res_expired.defect_reason.lower()

    # 3. Name mismatch defect
    mismatch_doc = DocumentPayload(
        doc_type=DocumentType.NATIONAL_ID,
        document_number="ID998877",
        raw_content="ID Card: Charles Montgomery",
        expiry_date="2032-12-31",
        holder_name="Charles Montgomery",
    )
    res_mismatch = extractor.extract_and_verify(
        mismatch_doc, declared_name="Edward Norton"
    )
    assert res_mismatch.defect_detected is True
    assert "Name mismatch" in res_mismatch.defect_reason

    # 4. Tampering defect
    tampered_doc = DocumentPayload(
        doc_type=DocumentType.PASSPORT,
        document_number="P000111",
        raw_content="[ALTERED] Passport Document: John Doe",
        expiry_date="2029-05-01",
        holder_name="John Doe",
    )
    res_tampered = extractor.extract_and_verify(tampered_doc, declared_name="John Doe")
    assert res_tampered.defect_detected is True
    assert "Security anomaly" in res_tampered.defect_reason


@pytest.mark.asyncio
async def test_clean_consumer_onboarding_pipeline():
    """Verify clean consumer applicant is assigned LOW risk and approved under A2 autonomy."""
    agent = OnboardingAgent()
    app = OnboardingApplicationRequest(
        applicant_type=ApplicantType.INDIVIDUAL,
        legal_name="Jennifer Clark",
        email="jennifer.clark@example.com",
        declared_dob="1992-08-20",
        declared_address="456 Elm St, New York, NY 10001",
        documents=[
            DocumentPayload(
                doc_type=DocumentType.PASSPORT,
                document_number="P77112233",
                raw_content="Passport of Jennifer Clark valid through 2031",
                expiry_date="2031-10-15",
                holder_name="Jennifer Clark",
            )
        ],
    )

    disposition = await agent.evaluate_application(app)
    assert disposition.legal_name == "Jennifer Clark"
    assert disposition.risk_rating == RiskRating.LOW
    assert disposition.recommended_action == "APPROVE"
    assert len(disposition.defects_found) == 0
    assert len(disposition.screening_hits) == 0


@pytest.mark.asyncio
async def test_defective_document_onboarding_escalates_to_a1_ticket():
    """Verify applicant with expired document is flagged HIGH risk and routes to Maker-Checker ticket."""
    agent = OnboardingAgent()
    app = OnboardingApplicationRequest(
        applicant_type=ApplicantType.INDIVIDUAL,
        legal_name="Marcus Aurelius",
        email="marcus@example.com",
        declared_address="1 Roman Forum, Rome, NY",
        documents=[
            DocumentPayload(
                doc_type=DocumentType.DRIVERS_LICENSE,
                document_number="DL994411",
                raw_content="Drivers License for Marcus Aurelius expired in 2021",
                expiry_date="2021-06-30",
                holder_name="Marcus Aurelius",
            )
        ],
    )

    disposition = await agent.evaluate_application(app)
    assert disposition.risk_rating == RiskRating.HIGH
    assert disposition.recommended_action == "ESCALATE_TO_ANALYST"
    assert disposition.status == ApplicationStatus.PENDING_HUMAN_REVIEW
    assert len(disposition.defects_found) > 0
    assert disposition.approval_ticket_id is not None

    # Check that an approval ticket was created in the approval inbox
    ticket = await approval_inbox.get_ticket(disposition.approval_ticket_id)
    assert ticket is not None
    assert ticket.status == TicketStatus.PENDING
    assert ticket.squad_name == "onboarding"
    assert "Marcus Aurelius" in ticket.arguments["legal_name"]

    # Analyst reviews and approves with exception note
    approved = await approval_inbox.approve_and_execute(
        ticket.id, reviewed_by="compliance_officer_sarah"
    )
    assert approved.status == TicketStatus.EXECUTED


@pytest.mark.asyncio
async def test_sanctioned_entity_corporate_onboarding_rejection():
    """Verify corporate applicant with sanctioned beneficial owner is flagged CRITICAL risk."""
    agent = OnboardingAgent()
    app = OnboardingApplicationRequest(
        applicant_type=ApplicantType.BUSINESS,
        legal_name="NorthStar Maritime Holdings Ltd",
        email="compliance@northstar.cy",
        declared_address="12 Harbor Way, Limassol, Cyprus",
        business_registration_number="REG-109283",
        declared_beneficial_owners=["Viktor Anatolyevich Petrov"],
        documents=[
            DocumentPayload(
                doc_type=DocumentType.COMPANY_REGISTRATION,
                document_number="REG-109283",
                raw_content="Company Registry Extract: NorthStar Maritime Holdings Ltd Beneficial Owners: Viktor Anatolyevich Petrov",
                expiry_date="2035-01-01",
                holder_name="NorthStar Maritime Holdings Ltd",
            )
        ],
    )

    disposition = await agent.evaluate_application(app)
    assert disposition.risk_rating == RiskRating.CRITICAL
    assert disposition.recommended_action == "REJECT"
    assert len(disposition.screening_hits) > 0
    assert any(h.list_type == "OFAC_SDN" for h in disposition.screening_hits)
    assert disposition.approval_ticket_id is not None
