"""Adversarial Verifier enforcing mandatory evidence citations in SAR narratives."""

import re
from typing import Dict, List, Set
from agent_platform.squads.aegis.models import CaseEvidence, CaseNarrative, VerificationResult


class NarrativeVerifier:
    """Adversarial compliance verifier ensuring every claim is backed by verified evidence."""

    def verify_narrative(
        self, narrative: CaseNarrative, evidence_store: Dict[str, CaseEvidence]
    ) -> VerificationResult:
        """Verify that all cited evidence IDs exist and all material claims have citations."""
        unsupported_claims: List[str] = []
        missing_ids: List[str] = []

        # 1. Extract all cited evidence tags from text using regex: [EVID-XXXX-...]
        cited_in_text: Set[str] = set(re.findall(r"\[(EVID-[\w\-]+)\]", narrative.detailed_chronology))
        for eid in narrative.cited_evidence_ids:
            cited_in_text.add(eid)

        if not cited_in_text:
            return VerificationResult(
                status="FAIL",
                verified=False,
                checked_claims_count=0,
                unsupported_claims=["Narrative contains zero cited evidence IDs. All SAR narratives mandate citations."],
                verifier_notes="Strict evidence-first policy violation: No evidence references found in narrative text.",
            )

        # 2. Verify existence of each cited evidence ID in evidence_store
        valid_citations = 0
        for eid in cited_in_text:
            if eid not in evidence_store:
                missing_ids.append(eid)
                unsupported_claims.append(f"Citation [{eid}] was cited in narrative but does not exist in the evidence store.")
            else:
                valid_citations += 1

        # 3. Check for unsupported paragraphs (paragraphs that assert facts without any citation)
        paragraphs = [p.strip() for p in narrative.detailed_chronology.split("\n\n") if p.strip()]
        for idx, p in enumerate(paragraphs):
            # If paragraph contains statements about money or transactions but has no [EVID-...] citation
            has_monetary_assertion = bool(re.search(r"(\$\d+|\btransfer\b|\bdeposit\b|\btransaction\b)", p, re.IGNORECASE))
            has_citation = bool(re.search(r"\[EVID-[\w\-]+\]", p))
            if has_monetary_assertion and not has_citation:
                unsupported_claims.append(
                    f"Paragraph #{idx + 1} makes transactional/monetary assertions without citing an evidence ID: \"{p[:80]}...\""
                )

        status = "PASS" if (len(unsupported_claims) == 0 and len(missing_ids) == 0) else "FAIL"

        return VerificationResult(
            status=status,
            verified=(status == "PASS"),
            checked_claims_count=valid_citations,
            unsupported_claims=unsupported_claims,
            missing_evidence_ids=missing_ids,
            verifier_notes=(
                "All factual assertions successfully mapped to verified evidence items."
                if status == "PASS"
                else f"Verifier rejected narrative: {len(unsupported_claims)} unsupported assertion(s) detected."
            ),
        )


verifier = NarrativeVerifier()
