"""Document Extraction and Defect Detection Engine for Onboarding & KYC."""

from datetime import date, datetime
import re
from typing import Optional
from agent_platform.squads.onboarding.models import (
    DocumentPayload,
    DocumentType,
    ExtractedDocumentData,
)
from agent_platform.squads.onboarding.watchlists import levenshtein_similarity, normalize_text


class DocumentExtractor:
    """Extracts structured identity fields and flags controlled defects."""

    def extract_and_verify(
        self, doc: DocumentPayload, declared_name: str, declared_dob: Optional[str] = None
    ) -> ExtractedDocumentData:
        """Extract fields and execute defect detection rules."""
        holder_name = doc.holder_name or declared_name
        expiry_str = doc.expiry_date

        defect_detected = False
        defect_reason = None
        is_expired = False

        # 1. Defect Check: Alteration / Tampering / Illegible text markers
        tamper_keywords = ["[ILLEGIBLE]", "[ALTERED]", "[TAMPERED]", "FORGED"]
        for kw in tamper_keywords:
            if kw in doc.raw_content:
                defect_detected = True
                defect_reason = f"Security anomaly detected: {kw} flag in document image"
                break

        # 2. Defect Check: Expiration date
        if expiry_str and not defect_detected:
            try:
                exp_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                if exp_date < date.today():
                    is_expired = True
                    defect_detected = True
                    defect_reason = f"Document expired on {expiry_str}"
            except ValueError:
                defect_detected = True
                defect_reason = f"Invalid expiry date format: {expiry_str}"

        # 3. Defect Check: Name mismatch between document and application
        if not defect_detected and doc.holder_name:
            sim = levenshtein_similarity(
                normalize_text(doc.holder_name), normalize_text(declared_name)
            )
            if sim < 0.80:
                defect_detected = True
                defect_reason = (
                    f"Name mismatch: Document states '{doc.holder_name}', "
                    f"but application declared '{declared_name}' (similarity: {sim:.2f})"
                )

        # 4. Extract corporate registration details if company registration doc
        reg_number = None
        beneficial_owners = []
        if doc.doc_type == DocumentType.COMPANY_REGISTRATION:
            reg_match = re.search(r"REG-\d{6,10}", doc.raw_content)
            reg_number = reg_match.group(0) if reg_match else doc.document_number
            # Check for listed owners in text
            if "Beneficial Owners:" in doc.raw_content:
                owners_part = doc.raw_content.split("Beneficial Owners:")[1].split("\n")[0]
                beneficial_owners = [o.strip() for o in owners_part.split(",") if o.strip()]

        return ExtractedDocumentData(
            document_id=doc.document_id,
            doc_type=doc.doc_type,
            full_name=holder_name,
            id_number=doc.document_number,
            dob=doc.holder_dob or declared_dob,
            expiry_date=expiry_str,
            registration_number=reg_number,
            beneficial_owners=beneficial_owners,
            is_expired=is_expired,
            defect_detected=defect_detected,
            defect_reason=defect_reason,
            confidence=0.98 if not defect_detected else 0.50,
        )


extractor = DocumentExtractor()
