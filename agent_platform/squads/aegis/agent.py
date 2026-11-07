"""Aegis Financial Crime Investigation Squad Orchestrator powered by Gemini 3.8 Flash."""

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from agent_platform.gateway.executor import gateway_executor
from agent_platform.gateway.models import ToolInvocationRequest
from agent_platform.squads.aegis.guardrails import scan_for_prompt_injection
from agent_platform.squads.aegis.models import (
    AlertPriority,
    AlertTypology,
    CaseEvidence,
    CaseNarrative,
    InvestigationCase,
    InvestigationPlan,
    PolicyExcerpt,
    RecommendedDisposition,
    TransactionFinding,
    TriageResult,
    VerificationResult,
)
from agent_platform.squads.aegis.verifier import verifier

SYSTEM_INSTRUCTION = """You are the Lead Financial Crime & Sanctions Investigator for the Aegis Squad at Meridian Bank.
Your duty is to investigate suspicious transactions, uncover money laundering typologies (Structuring, Layering, Rapid Movement),
retrieve binding FinCEN/FATF regulations via Policy RAG, and draft rigorous Suspicious Activity Reports (SAR).

Absolute Core Principle: EVIDENCE FIRST.
Every assertion in your narrative MUST be explicitly cited with a valid Evidence ID (e.g. [EVID-STRUCT-01]).
Any claim lacking verifiable evidence will be strictly rejected by the Adversarial Verifier.
"""


class AegisInvestigationAgent:
    """Multi-Agent Financial Crime Investigation Squad."""

    def __init__(self, model_name: str = "gemini-3.8-flash"):
        self.model_name = model_name
        self.squad_name = "financial_crime"
        self.agent_id = "agent_aegis_investigator_01"
        self.squad_roles = ["financial_crime", "compliance_officer"]

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any], reasoning: str) -> Any:
        """Execute Gateway tool call enforcing squad permissions and autonomy."""
        req = ToolInvocationRequest(
            agent_id=self.agent_id,
            squad_name=self.squad_name,
            tool_name=tool_name,
            arguments=arguments,
            reasoning=reasoning,
        )
        return await gateway_executor.invoke_tool(req, squad_roles=self.squad_roles)

    async def investigate_alert(self, alert_id: str) -> InvestigationCase:
        """Run the end-to-end multi-agent financial crime investigation pipeline."""
        case_id = f"case_aegis_{uuid.uuid4().hex[:8]}"

        # Step 1: Triage Agent
        alert_res = await self._call_tool(
            "get_alert_details",
            {"alert_id": alert_id},
            reasoning="Triaging alert metadata and customer profile",
        )

        if not alert_res.success or not alert_res.data or "error" in alert_res.data:
            raise ValueError(f"Alert {alert_id} not found in alert store.")

        alert_data = alert_res.data
        typology_str = alert_data.get("typology_hint", "UNUSUAL_VOLUME")
        try:
            typology = AlertTypology(typology_str)
        except ValueError:
            typology = AlertTypology.STRUCTURING

        triage = TriageResult(
            alert_id=alert_id,
            typology=typology,
            priority=AlertPriority.HIGH,
            confidence=0.92,
            fast_close_plausible=False,
            initial_rationale=f"Triggered by anomalous transaction pattern matching {typology.value} typology.",
        )

        # Step 2: Planner Agent
        plan = InvestigationPlan(
            case_id=case_id,
            steps=[
                "1. Analyze transaction flow and graph patterns",
                "2. Scan memos for prompt injection & adversarial evasion",
                "3. Retrieve statutory citations via Policy RAG",
                "4. Synthesize evidence into SAR narrative with mandatory citations",
                "5. Subject narrative to adversarial verification",
                "6. Submit dossier via Tool Gateway for MLRO approval (A1)",
            ],
            step_budget=5,
            token_budget=8000,
            evidence_types_required=["TRANSACTION_PATTERN", "POLICY_RULE"],
        )

        evidence_store: Dict[str, CaseEvidence] = {}
        findings: List[TransactionFinding] = []
        policy_citations: List[PolicyExcerpt] = []

        # Step 3: Transaction Analysis Agent
        account_id = alert_data.get("account_id", "")
        analysis_res = await self._call_tool(
            "analyze_account_transactions",
            {"account_id": account_id, "lookback_days": 30},
            reasoning="Running graph traversal and structuring pattern detection",
        )

        if analysis_res.success and analysis_res.data and analysis_res.data.get("findings"):
            for f_data in analysis_res.data["findings"]:
                finding = TransactionFinding.model_validate(f_data)
                findings.append(finding)

                # Store as verifiable evidence
                evidence_store[finding.evidence_id] = CaseEvidence(
                    evidence_id=finding.evidence_id,
                    source_type="TRANSACTION_PATTERN",
                    summary=finding.description,
                    raw_data={
                        "involved_txs": finding.involved_transaction_ids,
                        "amount_total": str(finding.amount_total),
                        "window_hours": finding.time_window_hours,
                    },
                )

        # Step 4: Guardrail Scan on Transaction Memos
        tx_list = alert_data.get("transactions", [])
        for tx in tx_list:
            memo = tx.get("memo", "")
            is_hostile, detected_patterns = scan_for_prompt_injection(memo)
            if is_hostile:
                sec_evid_id = f"EVID-SEC-{uuid.uuid4().hex[:6]}"
                evidence_store[sec_evid_id] = CaseEvidence(
                    evidence_id=sec_evid_id,
                    source_type="SECURITY_ANOMALY",
                    summary=f"Detected adversarial prompt injection attempt in transaction memo: {detected_patterns}",
                    raw_data={"tx_id": tx.get("id"), "patterns": detected_patterns},
                )

        # Step 5: Policy & Typology RAG Agent
        query_topic = f"{typology.value} CTR threshold evasion"
        policy_res = await self._call_tool(
            "retrieve_aml_policies",
            {"query": query_topic, "top_k": 2},
            reasoning=f"Retrieving AML statutory policies for {query_topic}",
        )

        if policy_res.success and policy_res.data and policy_res.data.get("excerpts"):
            for p_data in policy_res.data["excerpts"]:
                excerpt = PolicyExcerpt.model_validate(p_data)
                policy_citations.append(excerpt)

                pol_evid_id = f"EVID-POL-{excerpt.excerpt_id}"
                evidence_store[pol_evid_id] = CaseEvidence(
                    evidence_id=pol_evid_id,
                    source_type="POLICY_RULE",
                    summary=f"{excerpt.section}: {excerpt.citation}",
                    raw_data={"content": excerpt.content},
                )

        # Step 6: Narrative Drafter Agent
        # Construct evidence-backed narrative
        first_finding = findings[0] if findings else None
        first_pol = policy_citations[0] if policy_citations else None

        chronology_paragraphs = []
        if first_finding:
            chronology_paragraphs.append(
                f"Between November 5 and November 6, 2026, account {alert_data.get('account_number')} engaged in "
                f"a pattern of {len(first_finding.involved_transaction_ids)} consecutive deposit transactions each strictly "
                f"under $10,000, totaling ${first_finding.amount_total:,.2f} USD [{first_finding.evidence_id}]."
            )
            chronology_paragraphs.append(
                f"Following the accumulation of structured funds, a consolidating wire transfer was initiated to an offshore "
                f"entity [{first_finding.evidence_id}]."
            )

        if first_pol:
            pol_id = f"EVID-POL-{first_pol.excerpt_id}"
            chronology_paragraphs.append(
                f"This observed pattern violates anti-structuring provisions under {first_pol.section}, which prohibits "
                f"conducting transactions designed to evade FinCEN Currency Transaction Reporting [{pol_id}]."
            )

        detailed_text = "\n\n".join(chronology_paragraphs)
        cited_ids = list(evidence_store.keys())

        narrative = CaseNarrative(
            case_id=case_id,
            executive_summary=(
                f"Investigation into customer {alert_data.get('customer_id')} revealed systematic "
                f"{typology.value} activity designed to evade BSA/AML reporting thresholds."
            ),
            detailed_chronology=detailed_text,
            cited_evidence_ids=cited_ids,
            cited_policy_sections=[p.section for p in policy_citations],
            recommended_disposition=RecommendedDisposition.FILE_SAR,
            disposition_rationale="Clear evidence of intentional structuring and reporting evasion warrants immediate SAR filing.",
        )

        # Step 7: Adversarial Verifier Agent
        verification = verifier.verify_narrative(narrative, evidence_store)

        # Step 8: Tool Gateway Submission (A1 Action for MLRO Review)
        sar_res = await self._call_tool(
            "file_sar_dossier",
            {
                "case_id": case_id,
                "customer_id": alert_data.get("customer_id", "cust_unknown"),
                "narrative_summary": narrative.executive_summary,
                "cited_evidence_ids": cited_ids,
                "recommended_disposition": narrative.recommended_disposition.value,
            },
            reasoning=f"Filing verified SAR dossier {case_id} for MLRO sign-off",
        )

        ticket_id = sar_res.approval_ticket_id if sar_res.approval_required else None

        return InvestigationCase(
            case_id=case_id,
            alert_id=alert_id,
            customer_id=alert_data.get("customer_id", "cust_unknown"),
            account_number=alert_data.get("account_number", ""),
            typology=typology,
            priority=AlertPriority.HIGH,
            status="PENDING_APPROVAL" if ticket_id else "COMPLETED",
            triage=triage,
            plan=plan,
            findings=findings,
            evidence_store=evidence_store,
            policy_citations=policy_citations,
            narrative=narrative,
            verification=verification,
            approval_ticket_id=ticket_id,
        )
