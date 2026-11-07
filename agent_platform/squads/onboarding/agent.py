"""Onboarding & KYC Agent Squad powered by Gemini 3.8 Flash and Tool Gateway."""

import uuid
from typing import Any, Dict, List, Optional

from agent_platform.gateway.executor import gateway_executor
from agent_platform.gateway.models import ToolInvocationRequest
from agent_platform.squads.onboarding.models import (
    ApplicantType,
    ApplicationStatus,
    ExtractedDocumentData,
    OnboardingApplicationRequest,
    OnboardingDisposition,
    RiskRating,
    ScreeningMatch,
)

SYSTEM_INSTRUCTION = """You are the Senior Onboarding & Financial Crime Prevention Officer for Meridian Bank.
Your duty is to orchestrate KYC verification for new account applications:
1. Ingest identity documents, verify validity, and flag defects (expired, name mismatch, tampering).
2. Screen applicants and beneficial owners against OFAC, EU Sanctions, and PEP watchlists.
3. Verify corporate registry standing for commercial applicants.
4. Synthesize findings into a formal risk disposition (LOW, MEDIUM, HIGH, CRITICAL).
5. All high-risk or defective applications must be escalated to a human compliance officer via the Tool Gateway.
"""


class OnboardingAgent:
    """Multi-Agent Onboarding and KYC Specialist squad."""

    def __init__(self, model_name: str = "gemini-3.8-flash"):
        self.model_name = model_name
        self.squad_name = "onboarding"
        self.agent_id = "agent_onboarding_01"
        self.squad_roles = ["onboarding", "compliance_officer"]

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any], reasoning: str) -> Any:
        """Invoke Gateway tool with squad credentials and role check."""
        req = ToolInvocationRequest(
            agent_id=self.agent_id,
            squad_name=self.squad_name,
            tool_name=tool_name,
            arguments=arguments,
            reasoning=reasoning,
        )
        return await gateway_executor.invoke_tool(req, squad_roles=self.squad_roles)

    async def evaluate_application(
        self, application: OnboardingApplicationRequest, application_id: Optional[str] = None
    ) -> OnboardingDisposition:
        """Execute full onboarding verification pipeline."""
        app_id = application_id or f"app_{uuid.uuid4().hex[:8]}"
        defects: List[str] = []
        evidence: List[str] = []
        screening_hits: List[ScreeningMatch] = []
        extracted_docs: List[ExtractedDocumentData] = []

        # 1. Document Extraction & Defect Detection Step
        for doc in application.documents:
            res = await self._call_tool(
                "extract_document_fields",
                {
                    "doc_type": doc.doc_type.value,
                    "document_number": doc.document_number,
                    "raw_content": doc.raw_content,
                    "declared_applicant_name": application.legal_name,
                    "issuing_country": doc.issuing_country,
                    "expiry_date": doc.expiry_date,
                    "holder_name": doc.holder_name,
                    "declared_dob": application.declared_dob,
                },
                reasoning=f"Extracting fields and verifying validity of document {doc.document_id}",
            )
            if res.success and res.data:
                data = res.data
                doc_obj = ExtractedDocumentData.model_validate(data)
                extracted_docs.append(doc_obj)

                if doc_obj.defect_detected:
                    defects.append(f"{doc_obj.doc_type.value} [{doc_obj.id_number}]: {doc_obj.defect_reason}")
                else:
                    evidence.append(f"Verified valid {doc_obj.doc_type.value} issued by {doc.issuing_country}")

        # 2. Watchlist & Sanctions Screening Step
        names_to_screen = [application.legal_name]
        if application.applicant_type == ApplicantType.BUSINESS:
            names_to_screen.extend(application.declared_beneficial_owners)

        for name in set(names_to_screen):
            screen_res = await self._call_tool(
                "screen_entity_watchlists",
                {"name": name, "threshold": 0.80},
                reasoning=f"Performing sanctions and PEP fuzzy match screening for entity {name}",
            )
            if screen_res.success and screen_res.data and screen_res.data.get("matches"):
                for m in screen_res.data["matches"]:
                    match_obj = ScreeningMatch.model_validate(m)
                    screening_hits.append(match_obj)
                    defects.append(
                        f"Watchlist Hit: {match_obj.searched_query} matched {match_obj.matched_name} "
                        f"on {match_obj.list_type} (Score: {match_obj.match_score:.2f})"
                    )

        # 3. Corporate Registry Verification (for Businesses)
        if application.applicant_type == ApplicantType.BUSINESS and application.business_registration_number:
            reg_res = await self._call_tool(
                "verify_company_registry",
                {"registration_number": application.business_registration_number},
                reasoning=f"Verifying registration status for {application.business_registration_number}",
            )
            if reg_res.success and reg_res.data:
                reg_data = reg_res.data
                if not reg_data.get("found"):
                    defects.append(f"Company registration {application.business_registration_number} not found in state registry")
                elif reg_data.get("status") != "ACTIVE":
                    defects.append(f"Company status is {reg_data.get('status')} in registry")
                else:
                    evidence.append(f"Confirmed ACTIVE corporate status in {reg_data.get('jurisdiction')}")

        # 4. Synthesize Risk Rating & Action Recommendation
        has_sanctions = any(h.list_type in ("OFAC_SDN", "EU_SANCTIONS") for h in screening_hits)
        has_pep = any(h.list_type == "PEP" for h in screening_hits)

        if has_sanctions:
            risk = RiskRating.CRITICAL
            action = "REJECT"
            status = ApplicationStatus.PENDING_HUMAN_REVIEW
            rationale = "CRITICAL RISK: Entity matched an active OFAC/EU sanctions listing. Immediate escalation required."
        elif defects or has_pep:
            risk = RiskRating.HIGH
            action = "ESCALATE_TO_ANALYST"
            status = ApplicationStatus.PENDING_HUMAN_REVIEW
            rationale = (
                f"HIGH RISK: Application contains compliance defects or PEP exposure ({len(defects)} issue(s)). "
                "Human maker-checker review mandated under A1 autonomy."
            )
        else:
            risk = RiskRating.LOW
            action = "APPROVE"
            status = ApplicationStatus.APPROVED
            rationale = "LOW RISK: All identity documents verified, corporate active status confirmed, and zero watchlist hits."

        # 5. Submit Official Disposition via Tool Gateway (A1 Maker-Checker if High Risk / Defects)
        disposition_res = await self._call_tool(
            "submit_onboarding_disposition",
            {
                "application_id": app_id,
                "legal_name": application.legal_name,
                "risk_rating": risk.value,
                "action": action,
                "rationale": rationale,
                "defects_found": defects,
                "screening_hits": [h.model_dump() for h in screening_hits],
            },
            reasoning=rationale,
        )

        ticket_id = disposition_res.approval_ticket_id if disposition_res.approval_required else None

        return OnboardingDisposition(
            application_id=app_id,
            legal_name=application.legal_name,
            applicant_type=application.applicant_type,
            risk_rating=risk,
            recommended_action=action,
            confidence=0.98 if not defects else 0.65,
            evidence=evidence,
            defects_found=defects,
            screening_hits=screening_hits,
            approval_ticket_id=ticket_id,
            status=status,
            rationale=rationale,
        )
