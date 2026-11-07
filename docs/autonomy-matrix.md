# Autonomy Matrix & Ladders

The Aegis / Meridian platform operates on a bounded autonomy ladder. Every action an agent squad can execute via the MCP Tool Gateway has a strictly configured autonomy level:

| Level | Designation | Description | System Behavior | Example in Banking Core |
| :--- | :--- | :--- | :--- | :--- |
| **A0** | **Suggest** | Agent prepares an analysis or draft; a human operator must execute the action manually. | Proposal stored in DB; ops console notification raised; no tool execution until operator acts. | Drafting SAR narrative for AML alert investigation |
| **A1** | **Act with Approval** | Agent prepares a structured, validated action payload; execution is halted until approved by a human in the Ops Console. | Gateway holds execution; tickets generated in Ops Inbox; on approval, gateway signs & dispatches action. | Resubmitting a corrected payment exceeding auto-limit ($250+) |
| **A2** | **Act within Limits** | Agent executes autonomously within tight risk, amount, and frequency limits; execution is logged and sampled for human QA. | Gateway validates amount <= limit, checks rate limit, executes immediately, logs to audit stream with QA sampling tag. | Correcting formatting on a low-value transfer (<$250) |
| **A3** | **Fully Autonomous** | Agent executes with zero human in the loop. | **STRICTLY FORBIDDEN** for all money-movement and ledger balance mutations. | Read-only operations copilot answering operator questions |

## Autonomy Matrix by Squad

| Squad | Action Identifier | Allowed Level | Conditions / Thresholds |
| :--- | :--- | :--- | :--- |
| **Onboarding** | `onboarding.extract_documents` | A2 | Read-only document OCR & field extraction |
| **Onboarding** | `onboarding.screen_sanctions` | A2 | Automated screening against watchlists |
| **Onboarding** | `onboarding.approve_application` | A1 | Mandatory human approval for all account creations |
| **Payment Repair** | `payments.diagnose_failure` | A2 | Read-only inspection of ISO 20022 message & history |
| **Payment Repair** | `payments.repair_formatting` | A2 | If amount <= $250.00 and reversible |
| **Payment Repair** | `payments.resubmit_transfer` | A1 | Required if amount > $250.00 |
| **Financial Crime** | `aegis.analyze_transactions` | A2 | Read-only historical graph & typology evaluation |
| **Financial Crime** | `aegis.draft_case_narrative` | A0 | Generates cited narrative for human analyst review |
| **Financial Crime** | `aegis.freeze_account` | A1 | Mandatory compliance officer approval |
