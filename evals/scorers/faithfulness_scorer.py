"""Faithfulness and Evidence Citation Scorer (LLM-as-a-Judge)."""

from typing import Dict, List
from pydantic import BaseModel

from agent_platform.squads.aegis.models import CaseEvidence, CaseNarrative
from agent_platform.squads.aegis.verifier import verifier


class FaithfulnessMetrics(BaseModel):
    total_narratives_evaluated: int
    passed_verification_count: int
    failed_verification_count: int
    unsupported_claim_rate: float
    citation_accuracy: float
    average_citations_per_narrative: float


def compute_faithfulness_metrics(
    eval_cases: List[tuple[CaseNarrative, Dict[str, CaseEvidence]]]
) -> FaithfulnessMetrics:
    """Evaluate SAR narrative faithfulness and citation integrity across benchmark cases."""
    if not eval_cases:
        return FaithfulnessMetrics(
            total_narratives_evaluated=0,
            passed_verification_count=0,
            failed_verification_count=0,
            unsupported_claim_rate=0.0,
            citation_accuracy=1.0,
            average_citations_per_narrative=0.0,
        )

    passed = 0
    failed = 0
    total_unsupported = 0
    total_citations = 0

    for narrative, store in eval_cases:
        res = verifier.verify_narrative(narrative, store)
        total_citations += res.checked_claims_count
        if res.verified:
            passed += 1
        else:
            failed += 1
            total_unsupported += len(res.unsupported_claims)

    total = len(eval_cases)
    unsupported_rate = round(total_unsupported / max(total_citations + total_unsupported, 1), 4)
    citation_acc = round(passed / total, 4)
    avg_citations = round(total_citations / total, 2)

    return FaithfulnessMetrics(
        total_narratives_evaluated=total,
        passed_verification_count=passed,
        failed_verification_count=failed,
        unsupported_claim_rate=unsupported_rate,
        citation_accuracy=citation_acc,
        average_citations_per_narrative=avg_citations,
    )
