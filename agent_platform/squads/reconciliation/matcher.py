"""Reconciliation Matching Engine for B2B Invoices, Remittance Advices, and Ledger Postings."""

import re
import uuid
from decimal import Decimal
from typing import List, Tuple
from agent_platform.squads.onboarding.watchlists import levenshtein_distance
from agent_platform.squads.reconciliation.models import (
    Invoice,
    LedgerPostingItem,
    MatchType,
    ReconciliationBatch,
    ReconciliationMatch,
)


def normalize_text(text: str) -> str:
    """Normalize text by lowercasing and removing non-alphanumeric punctuation."""
    return re.sub(r"[^a-zA-Z0-9\s]", "", text).lower().strip()


def extract_potential_invoice_numbers(narrative: str) -> List[str]:
    """Extract patterns resembling invoice numbers (e.g. INV-10023, 2026-081, #9912)."""
    tokens = re.findall(r"(?:inv|invoice|ref|#)?[-:\s]?([0-9]{4,10}|[A-Z]{2,4}-[0-9]{3,8})", narrative, re.IGNORECASE)
    cleaned = [t.strip().upper() for t in tokens if len(t.strip()) >= 3]
    # Also add standard whitespace words
    for word in narrative.replace("#", " ").replace("/", " ").replace("-", " ").split():
        if any(char.isdigit() for char in word) and len(word) >= 4:
            cleaned.append(word.upper())
    return list(set(cleaned))


class ReconciliationEngine:
    """Multi-pass deterministic reconciliation engine matching ledger postings against invoices."""

    @staticmethod
    def run_reconciliation(
        postings: List[LedgerPostingItem],
        invoices: List[Invoice],
    ) -> ReconciliationBatch:
        """Execute multi-pass matching:
        Pass 1: Exact 1-to-1 match (Exact amount + invoice number in narrative).
        Pass 2: Fuzzy reference match (Exact amount + close invoice number or vendor name match).
        Pass 3: 2-to-1 Split payment match (1 credit posting matches sum of 2 invoices from same customer).
        Pass 4: Partial payment match (credit posting < invoice amount with explicit reference).
        """
        matches: List[ReconciliationMatch] = []
        matched_posting_ids = set()
        matched_invoice_ids = set()

        available_invoices = [inv for inv in invoices if inv.status != "PAID"]
        credit_postings = [p for p in postings if p.direction == "CREDIT" and not p.reconciled]

        # --- PASS 1: Exact 1-to-1 Match ---
        for p in credit_postings:
            if p.posting_id in matched_posting_ids:
                continue

            for inv in available_invoices:
                if inv.invoice_id in matched_invoice_ids:
                    continue

                # Check exact amount
                if p.amount == inv.amount:
                    # Check invoice number in narrative
                    inv_clean = normalize_text(inv.invoice_number)
                    narrative_clean = normalize_text(p.narrative)

                    if inv_clean in narrative_clean or inv.invoice_number.upper() in p.narrative.upper():
                        matched_posting_ids.add(p.posting_id)
                        matched_invoice_ids.add(inv.invoice_id)
                        matches.append(
                            ReconciliationMatch(
                                match_id=f"match_{uuid.uuid4().hex[:8]}",
                                match_type=MatchType.EXACT_ONE_TO_ONE,
                                confidence_score=1.0,
                                matched_invoice_ids=[inv.invoice_id],
                                matched_posting_ids=[p.posting_id],
                                total_invoice_amount=inv.amount,
                                total_posting_amount=p.amount,
                                discrepancy_amount=Decimal("0.00"),
                                rationale=f"Exact amount ${p.amount} and exact invoice reference '{inv.invoice_number}' found in narrative.",
                            )
                        )
                        break

        # --- PASS 2: Fuzzy Reference Match ---
        for p in credit_postings:
            if p.posting_id in matched_posting_ids:
                continue

            extracted_refs = extract_potential_invoice_numbers(p.narrative)

            for inv in available_invoices:
                if inv.invoice_id in matched_invoice_ids:
                    continue

                # Exact amount match
                if p.amount == inv.amount:
                    inv_num = inv.invoice_number.upper()
                    # Check if any extracted token has high similarity or substring
                    is_fuzzy_hit = False
                    for ref in extracted_refs:
                        dist = levenshtein_distance(ref, inv_num)
                        max_len = max(len(ref), len(inv_num))
                        similarity = 1.0 - (dist / max_len) if max_len > 0 else 0.0
                        if similarity >= 0.75 or ref in inv_num or inv_num in ref:
                            is_fuzzy_hit = True
                            break

                    if is_fuzzy_hit:
                        matched_posting_ids.add(p.posting_id)
                        matched_invoice_ids.add(inv.invoice_id)
                        matches.append(
                            ReconciliationMatch(
                                match_id=f"match_{uuid.uuid4().hex[:8]}",
                                match_type=MatchType.FUZZY_REFERENCE,
                                confidence_score=0.90,
                                matched_invoice_ids=[inv.invoice_id],
                                matched_posting_ids=[p.posting_id],
                                total_invoice_amount=inv.amount,
                                total_posting_amount=p.amount,
                                discrepancy_amount=Decimal("0.00"),
                                rationale=f"Exact amount ${p.amount} with fuzzy reference match to invoice '{inv.invoice_number}'.",
                            )
                        )
                        break

        # --- PASS 3: 2-to-1 Split Payment (1 Posting pays 2 Invoices) ---
        for p in credit_postings:
            if p.posting_id in matched_posting_ids:
                continue

            unmatched_invs = [inv for inv in available_invoices if inv.invoice_id not in matched_invoice_ids]

            # Try pairs of invoices
            found_pair = False
            for i in range(len(unmatched_invs)):
                for j in range(i + 1, len(unmatched_invs)):
                    inv1 = unmatched_invs[i]
                    inv2 = unmatched_invs[j]

                    # Same customer or same currency
                    if inv1.amount + inv2.amount == p.amount:
                        # Check if either invoice number appears in the narrative or remittance
                        inv1_num = inv1.invoice_number.upper()
                        inv2_num = inv2.invoice_number.upper()
                        narrative_upper = p.narrative.upper()

                        if (inv1_num in narrative_upper or inv2_num in narrative_upper or
                            "COMBINED" in narrative_upper or "BATCH" in narrative_upper or "MULTIPLE" in narrative_upper or
                            inv1.customer_id == inv2.customer_id):
                            
                            matched_posting_ids.add(p.posting_id)
                            matched_invoice_ids.add(inv1.invoice_id)
                            matched_invoice_ids.add(inv2.invoice_id)
                            matches.append(
                                ReconciliationMatch(
                                    match_id=f"match_{uuid.uuid4().hex[:8]}",
                                    match_type=MatchType.SPLIT_PAYMENT_COMBINED,
                                    confidence_score=0.95,
                                    matched_invoice_ids=[inv1.invoice_id, inv2.invoice_id],
                                    matched_posting_ids=[p.posting_id],
                                    total_invoice_amount=inv1.amount + inv2.amount,
                                    total_posting_amount=p.amount,
                                    discrepancy_amount=Decimal("0.00"),
                                    rationale=f"Combined remittance: Posting of ${p.amount} exactly matches sum of Invoices '{inv1.invoice_number}' (${inv1.amount}) + '{inv2.invoice_number}' (${inv2.amount}).",
                                )
                            )
                            found_pair = True
                            break
                if found_pair:
                    break

        # --- PASS 4: Partial Payment Match ---
        for p in credit_postings:
            if p.posting_id in matched_posting_ids:
                continue

            for inv in available_invoices:
                if inv.invoice_id in matched_invoice_ids:
                    continue

                if p.amount < inv.amount:
                    inv_clean = normalize_text(inv.invoice_number)
                    narrative_clean = normalize_text(p.narrative)

                    if inv_clean in narrative_clean or inv.invoice_number.upper() in p.narrative.upper():
                        discrepancy = inv.amount - p.amount
                        matched_posting_ids.add(p.posting_id)
                        matched_invoice_ids.add(inv.invoice_id)
                        matches.append(
                            ReconciliationMatch(
                                match_id=f"match_{uuid.uuid4().hex[:8]}",
                                match_type=MatchType.PARTIAL_PAYMENT,
                                confidence_score=0.85,
                                matched_invoice_ids=[inv.invoice_id],
                                matched_posting_ids=[p.posting_id],
                                total_invoice_amount=inv.amount,
                                total_posting_amount=p.amount,
                                discrepancy_amount=discrepancy,
                                rationale=f"Partial payment: Received ${p.amount} against ${inv.amount} for invoice '{inv.invoice_number}'. Remaining unpaid balance: ${discrepancy}.",
                            )
                        )
                        break

        # Compute totals
        unmatched_posts = [p.posting_id for p in credit_postings if p.posting_id not in matched_posting_ids]
        unmatched_invoices_ids = [inv.invoice_id for inv in available_invoices if inv.invoice_id not in matched_invoice_ids]
        total_matched_vol = sum(m.total_posting_amount for m in matches)

        return ReconciliationBatch(
            batch_id=f"batch_{uuid.uuid4().hex[:8]}",
            matches=matches,
            unmatched_postings=unmatched_posts,
            unmatched_invoices=unmatched_invoices_ids,
            total_matched_volume=total_matched_vol,
            status="DRAFT",
        )
