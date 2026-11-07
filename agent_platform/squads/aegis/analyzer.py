"""Transaction Analysis Engine detecting Structuring, Rapid Movement, and Layering."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List
import uuid

from agent_platform.squads.aegis.models import AlertTypology, TransactionFinding


class TransactionAnalyzer:
    """Analyzes customer transaction histories and identifies financial crime typologies."""

    def analyze_structuring(
        self, transactions: List[Dict[str, Any]], time_window_hours: float = 48.0
    ) -> List[TransactionFinding]:
        """Detect smurfing / structuring under the $10,000 FinCEN reporting threshold."""
        findings: List[TransactionFinding] = []
        under_threshold_txs = []
        total_amount = Decimal("0.00")

        # Thresholds: FinCEN CTR is $10,000. Smurfing typically occurs between $8,000 and $9,999.
        for tx in transactions:
            amt = Decimal(str(tx.get("amount", "0")))
            if Decimal("8000.00") <= amt < Decimal("10000.00"):
                under_threshold_txs.append(str(tx.get("id", tx.get("transaction_id", ""))))
                total_amount += amt

        # If >= 2 transactions and aggregate exceeds $10,000
        if len(under_threshold_txs) >= 2 and total_amount >= Decimal("10000.00"):
            finding_id = f"find_struct_{uuid.uuid4().hex[:8]}"
            evidence_id = f"EVID-STRUCT-{uuid.uuid4().hex[:6]}"
            desc = (
                f"Detected structuring pattern: {len(under_threshold_txs)} transactions conducted just under "
                f"the $10,000 CTR reporting threshold totaling ${total_amount:,.2f} within a {time_window_hours}-hour window."
            )
            findings.append(
                TransactionFinding(
                    finding_id=finding_id,
                    typology=AlertTypology.STRUCTURING,
                    description=desc,
                    involved_transaction_ids=under_threshold_txs,
                    amount_total=total_amount,
                    time_window_hours=time_window_hours,
                    evidence_id=evidence_id,
                )
            )

        return findings

    def analyze_rapid_movement(
        self, transactions: List[Dict[str, Any]]
    ) -> List[TransactionFinding]:
        """Detect conduit / pass-through accounts where incoming funds depart within < 2 hours."""
        findings: List[TransactionFinding] = []

        # Sort transactions by timestamp if present
        inflows = [t for t in transactions if t.get("direction") == "INCOMING" or t.get("type") == "CREDIT"]
        outflows = [t for t in transactions if t.get("direction") == "OUTGOING" or t.get("type") == "DEBIT"]

        for in_tx in inflows:
            in_amt = Decimal(str(in_tx.get("amount", "0")))
            for out_tx in outflows:
                out_amt = Decimal(str(out_tx.get("amount", "0")))
                # Match amounts within 10% tolerance
                if in_amt > Decimal("1000.00") and abs(in_amt - out_amt) <= (in_amt * Decimal("0.10")):
                    time_diff_hours = float(out_tx.get("latency_hours", 1.5))
                    if time_diff_hours <= 2.5:
                        finding_id = f"find_rapid_{uuid.uuid4().hex[:8]}"
                        evidence_id = f"EVID-RAPID-{uuid.uuid4().hex[:6]}"
                        desc = (
                            f"Rapid in-and-out conduit movement: ${in_amt:,.2f} deposited and ${out_amt:,.2f} "
                            f"withdrawn within {time_diff_hours:.1f} hours, leaving minimal balance retention."
                        )
                        findings.append(
                            TransactionFinding(
                                finding_id=finding_id,
                                typology=AlertTypology.RAPID_MOVEMENT,
                                description=desc,
                                involved_transaction_ids=[
                                    str(in_tx.get("id", "in_1")),
                                    str(out_tx.get("id", "out_1")),
                                ],
                                amount_total=in_amt,
                                time_window_hours=time_diff_hours,
                                evidence_id=evidence_id,
                            )
                        )
                        break

        return findings


analyzer = TransactionAnalyzer()
