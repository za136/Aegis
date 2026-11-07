# Aegis / Meridian: Agentic Payments & Banking Platform
## AI Agent & Developer Architecture Guide (GEMINI.md)

This file provides architectural context, domain invariants, and operational guidelines for AI models (including Google Gemini 3.8 Flash, Antigravity, and developer assistants) working on the Aegis / Meridian codebase.

---

## 1. Executive Summary

**Aegis / Meridian** is an enterprise-grade agentic payments and simulated banking platform. It bridges high-assurance deterministic financial core systems with generative AI agent squads governed by a Model Context Protocol (MCP) Tool Gateway, bounded autonomy ladders (A0–A3), and strict human-in-the-loop maker-checker controls.

### Key Governance Rule
> **Money movement, balance calculations, and accounting rules are NEVER delegated to LLMs.**
> The banking core is deterministic and mathematically enforced. LLM agents operate strictly at the *edge* via typed tools requiring explicit autonomy authorization.

---

## 2. Core Architecture Invariants

When reading, modifying, or extending this codebase, the following invariants MUST be preserved:

1. **Double-Entry Zero-Sum Invariant**:
   - Every financial transaction consists of an immutable `JournalEntry` with $\ge 2$ balanced `Posting` legs.
   - Mathematical balancing guarantee: `Sum(Debits) == Sum(Credits)`.
   - Never create or destroy money arbitrarily.

2. **Available Balance Invariant**:
   - `Available Balance = Settled Balance - Reserved Holds >= 0.00`.
   - Outgoing transfers place a two-phase `Hold` (`FUNDS_RESERVED`) before final settlement.

3. **Bounded Autonomy Ladders (ADR-002)**:
   - **A0 (Suggest)**: Agent drafts proposals or recommendations; human performs action manually.
   - **A1 (Act with Approval)**: Agent prepares write actions (transfers, SAR filings, provisional credit, batch reconciliation); held in `approval_inbox` until authorized by a human supervisor.
   - **A2 (Act within Limits)**: Agent executes autonomously within financial/policy ceilings (e.g. read operations, small balance inquiries).
   - **A3 (Fully Autonomous)**: Autonomous execution (explicitly blocked for money movements).

4. **Evidence-First Verification (Anti-Hallucination)**:
   - All factual assertions and financial claims drafted in Suspicious Activity Reports (SARs) must cite verified evidence tokens (e.g. `[EVID-...]`) stored in the evidence store. Uncited claims are rejected by the adversarial verifier.

5. **Security & Input Guardrails**:
   - All incoming narratives, payment memos, and transaction fields pass through injection scanners (`agent_platform/squads/aegis/guardrails.py`) to neutralize instruction override attacks before reaching LLMs.

---

## 3. Technology Stack

- **Model Layer**: Google Gemini 3.8 Flash (`gemini-3.8-flash`) via `@google/genai` Python SDK
- **Backend Services**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (asyncio + asyncpg / aiosqlite)
- **Dependency & Project Management**: `uv` (Fast Python package manager)
- **Frontend Portals**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide icons (npm workspaces)
- **Infrastructure & Storage**: PostgreSQL 16 with `pgvector`, Redis 7, Redpanda (single-node Kafka API with Schema Registry)
- **Platform & Delivery**: Docker Compose, Kubernetes (Helm v2), Terraform, Argo CD progressive rollouts

---

## 4. Repository Structure

```text
Aegis/
├── apps/
│   ├── customer-portal/         # Next.js 14 B2C/B2B Customer Banking Portal (:3000)
│   ├── ops-console/             # Next.js 14 Operations & Risk Governance Console (:3001)
│   └── api_gateway/             # Central FastAPI Gateway & BFF (:8000)
├── services/                    # Deterministic Banking Core
│   ├── accounts_ledger/         # Double-entry ledger, accounts, balances, holds
│   ├── identity/                # JWT authentication & Keycloak OIDC integration
│   ├── payments/                # Payment saga state machine (ISO 20022)
│   └── common/                  # DB sessions, configs, OpenTelemetry instrumentation
├── agent_platform/              # Agentic Edge & Governance
│   ├── gateway/                 # MCP Tool Gateway, registry, approvals, kill switch
│   └── squads/                  # Specialized Gemini 3.8 Flash Agent Squads
│       ├── onboarding/          # KYC applicant extraction, PEP/sanctions fuzzy matcher
│       ├── payment_repair/      # ISO 20022 exception diagnosis & automated repair
│       ├── aegis/               # AML crime investigation, policy RAG, SAR verifier
│       ├── reconciliation/      # B2B invoice & remittance multi-pass matching
│       ├── support_disputes/    # CFPB Reg E compliance & provisional credit
│       └── ops_copilot/         # Grounded operations copilot with citations
├── data/
│   └── generator/               # Deterministic synthetic bank data generator
├── evals/                       # CI evaluation benchmarks & golden datasets
├── infra/                       # Docker Compose, Helm charts, Terraform, GitOps
└── tests/                       # 11 comprehensive automated test suites
```

---

## 5. Development & Testing Commands

### Backend Setup & Execution (`uv`)
```bash
# Sync Python virtual environment
uv sync

# Generate synthetic bank data
uv run aegis-data --profile dev --output data/corpora/synthetic_dev.json

# Start API Gateway (Port 8000)
uv run uvicorn apps.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload

# Run all 11 automated test suites
uv run pytest -v

# Run non-negotiable CI Evaluation Gates
uv run aegis-eval --gate
```

### Frontend Portals Setup & Execution (`npm`)
```bash
# Install monorepo dependencies across all workspaces
npm install

# Start Customer Banking Portal (Port 3000)
npm run dev:customer

# Start Operations & Risk Console (Port 3001)
npm run dev:ops
```

---

## 6. Endpoints & UI Reference

- **Customer Banking Portal**: `http://localhost:3000` (Balances, Transfers, Digital Onboarding)
- **Operations & Risk Console**: `http://localhost:3001` (Command Center, Approvals Queue, Aegis SAR Workbench, Admin Controls)
- **API Gateway Root Index**: `http://localhost:8000/`
- **Interactive OpenAPI/Swagger**: `http://localhost:8000/docs`
- **Health Check Probe**: `http://localhost:8000/api/v1/health`
- **Prometheus Metrics**: `http://localhost:8000/metrics`
