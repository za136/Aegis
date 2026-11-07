"""ISO 20022 Payment Exception Reason Codes and Diagnostic Rules."""

from typing import Dict, Optional
from pydantic import BaseModel


class DiagnosticRule(BaseModel):
    code: str
    meaning: str
    repairable: bool
    suggested_strategy: str


# Comprehensive ISO 20022 Exception Knowledge Base
ISO_20022_ERROR_REGISTRY: Dict[str, DiagnosticRule] = {
    "AC04": DiagnosticRule(
        code="AC04",
        meaning="Account Closed at Beneficiary Bank",
        repairable=True,
        suggested_strategy="Query counterparty directory for updated active account number or replacement profile.",
    ),
    "AC01": DiagnosticRule(
        code="AC01",
        meaning="Incorrect Account Number or Checksum Failure",
        repairable=True,
        suggested_strategy="Validate IBAN/account structure, check for transposition errors, lookup counterparty registry.",
    ),
    "BE05": DiagnosticRule(
        code="BE05",
        meaning="Unrecognized Beneficiary Name",
        repairable=True,
        suggested_strategy="Perform fuzzy name matching against known trading entities and verify DBA aliases.",
    ),
    "AM04": DiagnosticRule(
        code="AM04",
        meaning="Insufficient Funds on Ledger",
        repairable=False,
        suggested_strategy="Double-entry invariant violation. Release hold or request customer fund account.",
    ),
    "RC01": DiagnosticRule(
        code="RC01",
        meaning="Bank Identifier Code (BIC) / Routing Invalid",
        repairable=True,
        suggested_strategy="Resolve correct clearing BIC/routing number from national clearinghouse table.",
    ),
}


def diagnose_rejection_code(code: str) -> Optional[DiagnosticRule]:
    """Lookup diagnostic rules for a payment failure code."""
    return ISO_20022_ERROR_REGISTRY.get(code.upper())
