# Aegis / Meridian Platform: Complete End-to-End Demo Walkthrough

## 1. Executive Summary & Architecture Overview
**Aegis / Meridian** is an enterprise agentic payments and simulated banking platform built on **Google Gemini 3.8 Flash** (`gemini-3.8-flash`) and **agy**. It demonstrates bounded autonomy ($A0$ to $A3$), multi-agent collaboration, double-entry financial ledger invariants, and zero-tolerance regulatory compliance.

### System Architecture Highlights:
- **Core Ledger**: Double-entry journal entries with two-phase holds (Pending $\rightarrow$ Settled).
- **Payment Saga**: Resilient payment execution with automatic ISO 20022 exception handling.
- **Bounded Tool Gateway**: MCP JSON-RPC protocol with strict role-based access and maker-checker approval ticketing.
- **Agent Squads**:
  1. *Payment Repair Squad*: Diagnoses AC04/BE05 rejections and proposes validated routing patches.
  2. *Onboarding & KYC Squad*: Extracts ID credentials, flags document tampering/expiry, and screens OFAC sanctions.
  3. *Aegis Financial Crime Squad*: Analyzes Smurfing/Structuring graphs, retrieves FinCEN policies, drafts SAR narratives, and adversarially audits citations.
  4. *B2B Reconciliation Squad*: Matches messy remittances, split payments (2-to-1), and credit postings.
  5. *Customer Support & Disputes Squad*: Enforces CFPB Regulation E (12 CFR Part 1005) and calculates liability.
  6. *Operations Copilot*: Answers complex operational queries with 100% grounded citations.
- **Observability & Governance**: OpenTelemetry span tracing, Prometheus metrics export (`/metrics`), Grafana dashboard, and live admin kill switches.

---

## 2. Interactive Step-by-Step Walkthrough

### Step 1: Customer Digital Onboarding & KYC Screening
- **Scenario**: A new customer applies for a business account with identity credentials.
- **Action**:
  1. Navigate to Customer Banking Portal: `http://localhost:3000/onboard`
  2. Input Applicant Details: `Alexander Petrov`, Business Type: `CORPORATION`, ID: `PASSPORT`.
  3. Click **Submit KYC Verification**.
- **Agent Trajectory (Onboarding Squad)**:
  - Invokes `extract_document_fields` $\rightarrow$ parses credential text and validity dates.
  - Invokes `screen_entity_watchlists` $\rightarrow$ calculates Levenshtein string distance against OFAC SDN and PEP lists.
  - Case with clean records auto-approves under **A2**; defective or high-risk cases escalate to **A1** ticket.
- **Verification**: Check Ops Console at `http://localhost:3001/onboarding` to inspect extracted entity data and risk disposition.

---

### Step 2: Double-Entry Ledger Transfer & Two-Phase Hold
- **Scenario**: Customer initiates an outbound transfer of $1,500.00.
- **API Call**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/payments/transfers \
    -H "Content-Type: application/json" \
    -d '{
      "source_account_id": "acc_usr_marcus_vance",
      "destination_account_id": "acc_beneficiary_delta",
      "amount": "1500.00",
      "currency": "USD",
      "reference": "Delta Logistics Consulting"
    }'
  ```
- **Ledger Invariant Check**:
  - Two-phase hold places `$1,500.00` in `reserved_holds` table (`available_balance` decreases; `settled_balance` unchanged).
  - Debit and Credit journal postings created simultaneously: $\sum \text{debits} \equiv \sum \text{credits}$.

---

### Step 3: Payment Exception Repair Squad (ISO 20022 AC04)
- **Scenario**: Outbound payment is rejected by receiving clearing bank with ISO 20022 code `AC04` (Account Closed).
- **Agent Trajectory (Payment Repair Squad)**:
  1. Trigger repair investigation: `POST /api/v1/payments/repair/pay_sample_101`.
  2. Agent queries `get_payment_details` to inspect the AC04 error message.
  3. Agent queries `lookup_counterparty_directory` for updated routing details for Delta Logistics.
  4. Agent formulates repair patch: substitutes obsolete routing `US33WELL9988111` with active account `US33WELL9988222`.
  5. Agent calls `propose_payment_repair` (Tier A1 write action) $\rightarrow$ creates Maker-Checker Ticket `appr_rep_01` in Ops Console!
- **Verification**: Open Approvals Queue (`http://localhost:3001/approvals`), review agent diagnosis, and click **Approve & Execute Repair**.

---

### Step 4: Aegis Financial Crime Squad (Structuring & SAR Verification)
- **Scenario**: Account receives three transactions of $9,500.00 within 24 hours to evade the $10,000 CTR reporting threshold.
- **Action**:
  1. Navigate to SAR Dossier Workbench: `http://localhost:3001/aegis`
  2. Open Alert `alert_smurf_001` (Structuring Typology).
  3. Click **Run Multi-Agent Investigation**.
- **Multi-Agent Pipeline Execution**:
  - *Triage & Planner*: Classifies typology as Smurfing/Structuring under 31 U.S.C. § 5324.
  - *Guardrail Scan*: Intercepts adversarial injection attempts in payment narratives.
  - *Policy RAG*: Retrieves exact FinCEN regulatory statutes and FFIEC narrative rules.
  - *Narrative Drafter*: Compiles SAR dossier with specific evidence tags (`[EVID-TX-01]`, `[EVID-ACCT-881]`).
  - *Adversarial Verifier*: Audits narrative. Every claim must have a valid evidence tag. Zero unevidenced assertions allowed.
  - *Tool Gateway*: Submits `file_sar_dossier` (A1 action) $\rightarrow$ routes to MLRO approval ticket.

---

### Step 5: B2B Remittance & 2-to-1 Split Payment Reconciliation
- **Scenario**: Corporate client wires $20,000.00 to pay two outstanding invoices: Invoice A ($12,500.00) and Invoice B ($7,500.00).
- **Action**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/reconciliation/run \
    -H "Content-Type: application/json" \
    -d '{"auto_submit_approval": true}'
  ```
- **Engine Logic**:
  - Pass 1 & 2: Checks 1-to-1 exact matches.
  - Pass 3: Identifies combined split payment where $12,500 + $7,500 \equiv $20,000.00.
  - Produces Reconciliation Batch and submits for accounting sign-off under Tier A1.

---

### Step 6: Customer Support & Reg E Dispute Resolution
- **Scenario**: Consumer Marcus Vance disputes an unauthorized card debit of $450.00.
- **Action**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/disputes/claims/disp_001/investigate
  ```
- **Reg E Engine Verification**:
  - Assesses compliance with 12 CFR Part 1005: notice within 60 days $\rightarrow$ eligible.
  - Calculates statutory consumer liability: capped at $50.00.
  - Recommends mandatory provisional credit of $450.00 under 12 CFR § 1005.11(c) pending 10-business-day investigation.
  - Creates ticket in Approvals Queue for supervisor sign-off.

---

### Step 7: Operations Copilot Live Querying
- **Scenario**: Operations analyst asks natural language questions in Ops Console.
- **Action**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/copilot/ask \
    -H "Content-Type: application/json" \
    -d '{"query": "What are our total customer deposits and how many approval tickets are pending?"}'
  ```
- **Response**:
  - Answers with verified numbers: `$18,450,230.50` deposits and `4` pending tickets.
  - Formats grounded citations: `[CITE:ledger_summary:deposits]` and `[CITE:approval_inbox:pending_count]`.
  - Provides instant navigation buttons: `View Live Ledger` and `Open Approvals Inbox`.

---

### Step 8: Platform Governance & Emergency Kill Switch
- **Scenario**: Emergency risk intervention requires halting all agent squads.
- **Action**:
  1. Navigate to Admin & Governance: `http://localhost:3001/admin`
  2. Click **ENGAGE EMERGENCY STOP**.
  3. Verify status: Banner turns red (`SYSTEM HALTED: EMERGENCY STOP ACTIVE`).
  4. Attempt any tool call: Tool Gateway immediately returns `Global emergency kill switch engaged`.
  5. Click **Disengage Emergency Stop** to resume normal operations.
- **Observability Verification**:
  - Access `/metrics` on API Gateway (`http://localhost:8000/metrics`) to observe live Prometheus counters.
  - Inspect Grafana dashboard (`infra/telemetry/dashboards/aegis-overview.json`) for multi-squad telemetry.
