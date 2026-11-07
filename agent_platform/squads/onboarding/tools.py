"""Registered Tool Gateway tools for the Onboarding & KYC Squad."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agent_platform.gateway.models import AutonomyLevel
from agent_platform.gateway.registry import register_tool
from agent_platform.squads.onboarding.extractor import extractor
from agent_platform.squads.onboarding.models import DocumentPayload, DocumentType
from agent_platform.squads.onboarding.watchlists import screen_name

# Synthetic Company Registry Directory
MOCK_COMPANY_REGISTRY = {
    "REG-109283": {
        "company_name": "Apex Cloud Technologies LLC",
        "jurisdiction": "Delaware, US",
        "status": "ACTIVE",
        "incorporation_date": "2021-04-12",
        "registered_agent": "Corporation Service Company",
    },
    "REG-881290": {
        "company_name": "Meridian Trading LLC",
        "jurisdiction": "New York, US",
        "status": "ACTIVE",
        "incorporation_date": "2019-11-05",
        "registered_agent": "National Registered Agents",
    },
    "REG-000404": {
        "company_name": "Defunct Shell Holdings Ltd",
        "jurisdiction": "Nevada, US",
        "status": "DISSOLVED",
        "incorporation_date": "2015-01-20",
        "registered_agent": "None",
    },
}

# In-memory application store
ONBOARDING_STORE: Dict[str, Dict[str, Any]] = {}


class ExtractDocumentArgs(BaseModel):
    doc_type: DocumentType
    document_number: str
    issuing_country: str = "US"
    raw_content: str
    expiry_date: Optional[str] = None
    holder_name: Optional[str] = None
    declared_applicant_name: str
    declared_dob: Optional[str] = None


@register_tool(
    name="extract_document_fields",
    description="Extract structured identity fields from identity documents and detect expiration or name defect anomalies.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["onboarding", "compliance_officer"],
    schema_model=ExtractDocumentArgs,
)
def extract_document_fields(
    doc_type: DocumentType,
    document_number: str,
    raw_content: str,
    declared_applicant_name: str,
    issuing_country: str = "US",
    expiry_date: Optional[str] = None,
    holder_name: Optional[str] = None,
    declared_dob: Optional[str] = None,
) -> Dict[str, Any]:
    payload = DocumentPayload(
        doc_type=doc_type,
        document_number=document_number,
        issuing_country=issuing_country,
        raw_content=raw_content,
        expiry_date=expiry_date,
        holder_name=holder_name,
        holder_dob=declared_dob,
    )
    extracted = extractor.extract_and_verify(
        payload, declared_name=declared_applicant_name, declared_dob=declared_dob
    )
    return extracted.model_dump()


class ScreenEntityArgs(BaseModel):
    name: str = Field(..., description="Full legal name of the individual or organization to screen")
    threshold: float = Field(default=0.80, description="Fuzzy match threshold between 0.0 and 1.0")


@register_tool(
    name="screen_entity_watchlists",
    description="Screen individual or corporate names against OFAC, EU Sanctions, and Politically Exposed Persons (PEP) lists.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["onboarding", "financial_crime", "compliance_officer"],
    schema_model=ScreenEntityArgs,
)
def screen_entity_watchlists(name: str, threshold: float = 0.80) -> Dict[str, Any]:
    hits = screen_name(name, threshold=threshold)
    return {
        "query": name,
        "hits_count": len(hits),
        "matches": [h.model_dump() for h in hits],
        "has_sanctions_match": any(h.list_type in ("OFAC_SDN", "EU_SANCTIONS") for h in hits),
        "has_pep_match": any(h.list_type == "PEP" for h in hits),
    }


class VerifyRegistryArgs(BaseModel):
    registration_number: str = Field(..., description="Corporate registration number, e.g., REG-109283")


@register_tool(
    name="verify_company_registry",
    description="Lookup official secretary of state or company registry to confirm corporate active status.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["onboarding", "compliance_officer"],
    schema_model=VerifyRegistryArgs,
)
def verify_company_registry(registration_number: str) -> Dict[str, Any]:
    reg = MOCK_COMPANY_REGISTRY.get(registration_number)
    if not reg:
        return {"found": False, "registration_number": registration_number, "status": "NOT_FOUND"}
    return {"found": True, "registration_number": registration_number, **reg}


class OnboardingDispositionArgs(BaseModel):
    application_id: str
    legal_name: str
    risk_rating: str  # LOW, MEDIUM, HIGH, CRITICAL
    action: str  # APPROVE, REJECT, ESCALATE_TO_ANALYST
    rationale: str
    defects_found: List[str] = Field(default_factory=list)
    screening_hits: List[Dict[str, Any]] = Field(default_factory=list)


@register_tool(
    name="submit_onboarding_disposition",
    description="Record official onboarding decision and create customer account or route high-risk/defect cases to human review.",
    autonomy_level=AutonomyLevel.A1_ACT_WITH_APPROVAL,
    is_write=True,
    required_squad_roles=["onboarding"],
    schema_model=OnboardingDispositionArgs,
)
def submit_onboarding_disposition(
    application_id: str,
    legal_name: str,
    risk_rating: str,
    action: str,
    rationale: str,
    defects_found: Optional[List[str]] = None,
    screening_hits: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    defects = defects_found or []
    hits = screening_hits or []

    # Final execution when approved
    ONBOARDING_STORE[application_id] = {
        "application_id": application_id,
        "legal_name": legal_name,
        "risk_rating": risk_rating,
        "action": action,
        "rationale": rationale,
        "status": "APPROVED" if action == "APPROVE" else "REJECTED",
        "defects": defects,
        "screening_hits": hits,
    }
    return {
        "success": True,
        "application_id": application_id,
        "status": ONBOARDING_STORE[application_id]["status"],
        "message": f"Onboarding disposition executed for {legal_name} (Action: {action}).",
    }
