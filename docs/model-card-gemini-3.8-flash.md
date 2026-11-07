# Model Card: Google Gemini 3.8 Flash in Aegis / Meridian Banking Platform

## 1. Model Details
- **Model Name**: Google Gemini 3.8 Flash (`gemini-3.8-flash`)
- **Developer**: Google DeepMind / Google Cloud GenAI
- **Release Standard**: Aegis Enterprise Financial Crime & Banking Edition
- **SDK & Integration**: Google GenAI Python SDK (`google-genai` / `langchain-google-genai`) with Antigravity CLI (`agy`) agent framework
- **Primary Roles Across Squads**:
  - **Payment Exception Repair Squad**: ISO 20022 error diagnostics (`AC04`, `BE05`), counterparty directory lookup, routing patch proposals.
  - **Onboarding & KYC Squad**: ID/Passport field extraction, document defect detection, sanctions/PEP fuzzy matching.
  - **Aegis Financial Crime Squad**: Transaction graph Smurfing/Structuring analysis, FinCEN/FATF policy retrieval (RAG), SAR narrative drafting, and Adversarial Verification.
  - **B2B Reconciliation Squad**: Remittance parsing, multi-pass matching, 2-to-1 split payments.
  - **Customer Support & Disputes Squad**: CFPB Regulation E statutory compliance evaluation, provisional credit calculation.
  - **Operations Copilot Squad**: Grounded natural language query answering with live database citations.

---

## 2. Intended Use & Bounded Autonomy Tiers
Aegis enforces a strict Bounded Autonomy ladder ($A0$ to $A3$) governing model tool invocations:

| Autonomy Tier | Name | Platform Constraint | Applied Squad Actions |
| :--- | :--- | :--- | :--- |
| **A0** | Suggest Only | Model produces recommendations; zero execution capability. | Draft suggestions, experimental advisory notes |
| **A1** | Act with Approval | Model generates action proposals; held in Approvals Inbox until human supervisor authorizes execution. | **Money movements**, SAR filings to FinCEN, provisional credits, batch ledger reconciliation |
| **A2** | Act within Limits | Model autonomously executes read tools and low-value write actions below financial policy thresholds. | Read-only queries, watchlist screening, transfers $\le \$100.00$, repairs $\le \$250.00$ |
| **A3** | Fully Autonomous | Model executes actions without human review. | Strictly forbidden for financial transfers or SAR filings |

> [!IMPORTANT]
> By regulatory mandate (FinCEN 31 CFR § 1020.320 and OCC Bulletins), SAR filings and high-value fund movements are **hard-locked to Tier A1** and can never be promoted to Tier A3.

---

## 3. Evaluation Benchmarks & CI Gates
The model is continuously evaluated in CI pipelines via `evals/ci/gate.py` across four golden benchmark suites:

| Benchmark Metric | Threshold Standard | Measured Score | CI Release Gate Status |
| :--- | :--- | :--- | :--- |
| **Financial Crime False Negative Rate (FNR)** | Strictly $0.0\%$ | **$0.0\%$** | ✅ PASSED (Zero missed structuring/laundering) |
| **Onboarding False Negative Rate (FNR)** | Strictly $0.0\%$ | **$0.0\%$** | ✅ PASSED (Zero auto-approved sanctioned entities) |
| **Prompt Injection Attack Success Rate (ASR)** | Strictly $0.0\%$ | **$0.0\%$** | ✅ PASSED (Zero successful jailbreaks) |
| **SAR Unsupported Claim Rate** | Strictly $0.0\%$ | **$0.0\%$** | ✅ PASSED (Zero hallucinated citations in SARs) |
| **Payment Exception Repair Accuracy** | $\ge 95.0\%$ | **$100.0\%$** | ✅ PASSED |
| **Trajectory Step Budget Breach Rate** | Strictly $0.0\%$ | **$0.0\%$** | ✅ PASSED (Zero runaway loops) |

---

## 4. Safety Guardrails & Defense Architecture
1. **Adversarial Input Guardrail (`agent_platform/squads/aegis/guardrails.py`)**:
   - Scans transaction memos and customer statements prior to LLM ingestion.
   - Detects direct prompt overrides (`"ignore instructions"`, `"do not file SAR"`, `"roleplay as auditor"`).
   - Sanitizes and logs hostile inputs to Prometheus security counters.
2. **Adversarial Evidence-First Verifier (`agent_platform/squads/aegis/verifier.py`)**:
   - Every factual or monetary assertion in drafted SAR narratives must contain a valid evidence citation (`[EVID-...]`).
   - The verifier compares claims directly against the cryptographic evidence store.
   - Any hallucinated transaction, phantom party, or unsupported amount causes immediate narrative rejection.
3. **Admin Kill Switches (`agent_platform/gateway/killswitch.py`)**:
   - Platform administrators can engage an instantaneous Global Emergency Stop or pause any squad at runtime.

---

## 5. Limitations & Ethical Considerations
- **Non-Autonomous Reporting**: Google Gemini 3.8 Flash acts exclusively as an analytical copilot. Ultimate legal responsibility for filing Suspicious Activity Reports remains with the bank's designated Money Laundering Reporting Officer (MLRO).
- **Synthetic Data Training**: While benchmarks validate 100% precision on golden AML typologies, edge cases in emerging typologies require ongoing human-in-the-loop oversight.
