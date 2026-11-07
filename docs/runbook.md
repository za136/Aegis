# Production Incident Response Runbook: Aegis / Meridian Platform

## 1. Overview & Operational Roles
This runbook governs operations for:
- **Site Reliability Engineers (SRE)**: Cluster infrastructure, ingress routing, database performance, and pod lifecycle.
- **Compliance & MLRO Team**: Approvals queue management, SAR filing authorizations, and AML triage.
- **Payment Operations Analysts**: Payment exception repair, B2B reconciliation batches, and Reg E dispute resolution.

---

## 2. Playbook 1: Engaging Emergency Kill Switches
### Trigger Conditions
- Widespread prompt injection exploitation detected in transaction logs.
- Unexpected runaway LLM token consumption or model latency spikes (> 10s).
- Regulatory halt ordered by FinCEN, OCC, or senior bank executive.

### Resolution Steps
1. **Engage Global Emergency Stop via Ops Console**:
   - Navigate to `https://ops.meridian.bank/admin`.
   - Click **ENGAGE EMERGENCY STOP**.
   - Input operator identification and regulatory/incident rationale.
2. **Alternative CLI / API Emergency Command**:
   ```bash
   curl -X POST https://api.meridian.bank/api/v1/admin/killswitch/global \
     -H "Content-Type: application/json" \
     -d '{"enabled": true, "reason": "Incident #INC-991: Hostile injection payload outbreak", "operator_id": "op_sre_oncall"}'
   ```
3. **Verify Halting**:
   - Check `https://api.meridian.bank/api/v1/admin/killswitch` — verify `"global_emergency_stop": true`.
   - All agent squads will immediately reject tool calls with error: `"Global emergency kill switch engaged"`.
   - Core banking payments continue normally; only autonomous agent loops are frozen.
4. **Resumption**:
   - Once the vulnerability is patched, click **Disengage Emergency Stop** in `/admin`.

---

## 3. Playbook 2: Triage of SAR Adversarial Verifier Rejections
### Trigger Conditions
- Prometheus alert: `aegis_verifier_rejections_total > 0`.
- Aegis squad reports SAR narrative rejection due to unevidenced claims.

### Resolution Steps
1. **Locate Rejected Case Dossier**:
   - Navigate to `https://ops.meridian.bank/aegis`.
   - Filter by status `VERIFICATION_FAILED`.
2. **Review Verification Audit Report**:
   - Inspect the verifier output highlighting specific ungrounded assertions.
   - Example rejection: `"Claim '$42,500.00 wired to Panamanian shell entity' cites non-existent evidence ID [EVID-PAN-01]"`.
3. **Determine Cause**:
   - *Hallucination*: Model fabricated details not in the transaction graph.
   - *Missing Tool Call*: Agent failed to retrieve counterparty directory entry before drafting.
4. **Resolution**:
   - Click **Re-investigate with Strict Grounding** in the Ops Console.
   - If the issue persists, downgrade Aegis squad autonomy to `A0` (Suggest Only) and notify platform engineering.

---

## 4. Playbook 3: Double-Entry Ledger Invariant Violation Alert
### Trigger Conditions
- Alert: `meridian_ledger_unbalanced_entries > 0` or database check failure: `sum(debits) != sum(credits)`.

### Resolution Steps
1. **Critical Severity**: P1 Stop Ship / Financial Freeze.
2. **Inspect Failed Journal Entry**:
   ```sql
   SELECT journal_entry_id, transaction_id, sum(amount) FILTER (WHERE direction = 'DEBIT') as debits,
          sum(amount) FILTER (WHERE direction = 'CREDIT') as credits
   FROM journal_postings
   GROUP BY journal_entry_id, transaction_id
   HAVING sum(amount) FILTER (WHERE direction = 'DEBIT') != sum(amount) FILTER (WHERE direction = 'CREDIT');
   ```
3. **Inspect Two-Phase Holds Table**:
   - Verify if an orphaned pending reservation hold exists without corresponding settlement.
4. **Remediation**:
   - Execute saga compensation rollback:
     `payment_saga.rollback_payment(payment_id)`.
   - Release hold: `ledger_engine.release_hold(hold_id)`.

---

## 5. Playbook 4: Progressive Canary Rollout Regression & Instant Rollback
### Trigger Conditions
- Argo CD Rollout canary step experiences error rate spike > 1.0% or latency > 500ms.

### Resolution Steps
1. **Inspect Rollout Status**:
   ```bash
   kubectl argo rollouts status api-gateway-canary -n meridian-core
   ```
2. **Abort & Rollback Canary Instantly**:
   ```bash
   kubectl argo rollouts abort api-gateway-canary -n meridian-core
   kubectl argo rollouts undo api-gateway-canary -n meridian-core
   ```
3. **Verify Traffic Shift**:
   - Verify NGINX Ingress routes 100% of traffic back to the stable replica deployment.
