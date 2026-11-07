# Aegis / Meridian Platform — Run & Operations Guide

This document provides complete, step-by-step instructions for installing, configuring, running, testing, and demonstrating the entire **Aegis / Meridian Agentic Payments and Banking Platform**.

---

## 1. System Requirements & Prerequisites

Ensure the following tools are installed on your host machine:

| Requirement | Minimum Version | Purpose |
| :--- | :--- | :--- |
| **Python** | `3.12+` | Backend services, agent platform, evaluators |
| **uv** | `0.4+` | High-speed Python package manager (`curl -LsSf https://astral.sh/uv/install.sh \| sh`) |
| **Node.js** | `18.0+` (or `20.0+` LTS) | Next.js Customer Portal and Operations Console |
| **npm** | `9.0+` | Monorepo package manager for frontend portals |
| **Docker & Compose** | `24.0+` / Compose `v2+` | PostgreSQL with `pgvector`, Redis 7, Redpanda broker |
| **Google Gemini API Key** | — | Powers Gemini 3.8 Flash (`gemini-3.8-flash`) across agent squads |

---

## 2. Port Reference Table

| Service / Application | Host Port | Protocol | Purpose / URL |
| :--- | :--- | :--- | :--- |
| **Customer Banking Portal** | `3000` | HTTP | Customer Dashboard, Transfers, Onboarding: `http://localhost:3000` |
| **Operations & Risk Console** | `3001` | HTTP | Ops Command Center, Approvals Queue, SAR Workbench, Admin: `http://localhost:3001` |
| **Central API Gateway** | `8000` | HTTP | FastAPI REST API & MCP Gateway: `http://localhost:8000` |
| **Swagger / OpenAPI Docs** | `8000` | HTTP | Interactive API Documentation: `http://localhost:8000/docs` |
| **Prometheus Metrics** | `8000` | HTTP | Platform & Agent Telemetry: `http://localhost:8000/metrics` |
| **PostgreSQL 16 (pgvector)**| `5432` | TCP | Ledger, accounts, holds, and AML embeddings |
| **Redis 7** | `6379` | TCP | Session store and fast caching |
| **Redpanda Broker** | `9092` | TCP | Kafka-compatible event streaming |
| **Redpanda Console** | `8085` | HTTP | Real-time topic and message browser: `http://localhost:8085` |
| **Keycloak OIDC (Optional)**| `8080` | HTTP | Enterprise Single Sign-On: `http://localhost:8080` |

---

## 3. Step-by-Step Setup & Execution

### Step 1: Clone and Configure Environment

```bash
cd /home/zabedin/projects/Aegis

# Copy environment variables
cp .env.example .env

# Edit .env and set your Google Gemini API key:
# GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### Step 2: Launch Local Infrastructure

Start the PostgreSQL (with `pgvector`), Redis, and Redpanda containers:

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

Verify that all containers are healthy:
```bash
docker compose -f infra/docker/docker-compose.yml ps
```

*(Optional: To run with Keycloak OIDC, append `--profile oidc`)*

### Step 3: Install Python Dependencies & Generate Data

```bash
# Install all backend dependencies into virtualenv via uv
uv sync

# Generate deterministic synthetic bank dataset (100 customers, 1000+ txs, labeled AML typologies)
uv run python -m data.generator.cli --profile dev --output data/corpora/synthetic_dev.json
```

### Step 4: Launch the Central API Gateway

Run the FastAPI API Gateway on port `8000`:

```bash
uv run uvicorn apps.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify backend health:
```bash
curl http://localhost:8000/api/v1/health
# Response: {"status":"healthy","service":"aegis-api-gateway","version":"0.1.0"}
```
Explore the interactive Swagger UI at **`http://localhost:8000/docs`**.

### Step 5: Install and Launch Frontend Portals

In a new terminal, install frontend dependencies and start both portals:

```bash
# Install workspace dependencies from the repo root
npm install

# Option A: Start both applications concurrently
npm run dev:customer & npm run dev:ops

# Option B: Run in separate terminals
# Terminal 2: Customer Banking Portal (Port 3000)
npm run dev:customer

# Terminal 3: Operations & Compliance Console (Port 3001)
npm run dev:ops
```

Once running:
- **Customer Portal**: Open `http://localhost:3000`
- **Operations Console**: Open `http://localhost:3001`

---

## 4. Running Automated Tests & Evaluation CI Gates

### Run All 11 Unit and Integration Test Suites

Execute the comprehensive test suite across ledger, gateway, squads, evals, and infrastructure:

```bash
uv run pytest -v
```

All 11 test suites should report **100% PASS**:
1. `tests/test_ledger.py` — Double-entry math invariants and available balance properties.
2. `tests/test_generator.py` — Deterministic bank data generation and planted AML typologies.
3. `tests/test_walking_skeleton.py` — End-to-end payment saga with two-phase holds.
4. `tests/test_tool_gateway.py` — MCP tool execution, permissions, and A1 Maker-Checker tickets.
5. `tests/test_payment_repair.py` — ISO 20022 error diagnostics and directory lookups.
6. `tests/test_onboarding_squad.py` — Document defect detection and OFAC sanctions screening.
7. `tests/test_aegis_squad.py` — Adversarial prompt injection defense, policy RAG, and cited SAR verifier.
8. `tests/test_evals_harness.py` — Binary outcome scoring, safety scoring, and trajectory metrics.
9. `tests/test_platform_infrastructure.py` — Prometheus metrics, OpenTelemetry spans, Helm, Terraform.
10. `tests/test_stretch_squads.py` — B2B reconciliation, Reg E dispute engine, Ops Copilot, bulk payments.
11. `tests/test_hardening_polish.py` — Emergency kill switches, per-squad pause, and autonomy ceiling clamping.

### Run the CI Benchmark Release Gate

Evaluate the agent squads against non-negotiable regulatory and safety thresholds:

```bash
uv run aegis-eval --gate
```

**Non-Negotiable Release Thresholds Enforced:**
- 🛡️ Financial Crime FNR: `0.0%` (Zero tolerance for undetected money laundering)
- 🛂 Onboarding FNR: `0.0%` (Zero tolerance for approving bad actors)
- 🔒 Prompt Injection Attack Success Rate (ASR): `0.0%` (Zero tolerance for jailbreaks)
- 📝 SAR Narrative Unsupported Claim Rate: `0.0%` (Zero tolerance for hallucinations)
- ⚙️ Payment Exception Repair Accuracy: `≥ 95.0%`
- ⏱️ Trajectory Step Budget Breaches: `0.0%`

---

## 5. Testing the Squads via API (cURL Examples)

### 1. Customer Digital Onboarding & KYC Screening
```bash
curl -X POST http://localhost:8000/api/v1/onboarding/apply \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_type": "INDIVIDUAL",
    "legal_name": "Marcus Aurelius",
    "email": "marcus@example.com",
    "declared_dob": "1988-04-26",
    "declared_address": "1 Roman Forum, Rome, NY",
    "documents": [
      {
        "doc_type": "PASSPORT",
        "document_number": "P12345678",
        "raw_content": "Passport of Marcus Aurelius valid through 2032",
        "expiry_date": "2032-10-15",
        "holder_name": "Marcus Aurelius"
      }
    ]
  }'
```

### 2. Double-Entry Ledger Transfer & Two-Phase Hold
```bash
curl -X POST http://localhost:8000/api/v1/payments/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "transfer_demo_001",
    "source_account_id": "00000000-0000-0000-0000-000000000001",
    "destination_account_id": "00000000-0000-0000-0000-000000000002",
    "amount": "1500.00",
    "currency": "USD",
    "description": "Supplier Invoice Settlement"
  }'
```

### 3. Aegis Financial Crime Investigation (Structuring SAR)
```bash
curl -X POST http://localhost:8000/api/v1/aegis/investigate/alt_struct_001
```

### 4. Operations Copilot Grounded Query
```bash
curl -X POST http://localhost:8000/api/v1/copilot/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is our customer deposit balance and how many approval tickets are pending?"
  }'
```

### 5. Admin Emergency Kill Switch (Global Stop)
```bash
# Engage emergency stop
curl -X POST http://localhost:8000/api/v1/admin/killswitch/global/engage \
  -H "Content-Type: application/json" \
  -d '{"reason": "Regulatory freeze drill", "operator_id": "lead_sre"}'

# Check status
curl http://localhost:8000/api/v1/admin/killswitch/status

# Disengage emergency stop
curl -X POST http://localhost:8000/api/v1/admin/killswitch/global/disengage \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "lead_sre"}'
```

---

## 6. Frontend Navigation & Pages

- **Customer Banking Portal (`http://localhost:3000`)**:
  - `/` — Customer dashboard with live settled and available balances.
  - `/accounts` — Account details, ledger history, and active holds.
  - `/transfer` — Initiate two-phase transfer with client idempotency key.
  - `/onboard` — Digital customer application with real-time risk feedback.

- **Operations & Risk Console (`http://localhost:3001`)**:
  - `/` — Command Center with platform KPIs and squad statuses.
  - `/monitor` — Live payment lifecycle timeline.
  - `/approvals` — Tier A1 Human-in-the-Loop review queue.
  - `/onboarding` — KYC investigation queue and defect telemetry.
  - `/aegis` — SAR Dossier Workbench with cited narrative verification.
  - `/admin` — Global emergency stop, per-squad toggles, and dynamic autonomy controls.

---

## 7. Production Deployment (Docker & Kubernetes)

### Production Docker Containers
```bash
# Build API Gateway
docker build -f infra/docker/Dockerfile.api-gateway -t meridian/api-gateway:latest .

# Build Customer Portal
docker build -f infra/docker/Dockerfile.customer-portal -t meridian/customer-portal:latest .

# Build Ops Console
docker build -f infra/docker/Dockerfile.ops-console -t meridian/ops-console:latest .
```

### Kubernetes Helm Chart
Deploy to Kubernetes with namespace isolation and network boundary egress control:
```bash
helm upgrade --install aegis infra/helm/aegis-platform \
  --namespace meridian-core \
  --create-namespace \
  -f infra/helm/aegis-platform/values.yaml
```

---

## 8. Interactive Demo Walkthrough

For a step-by-step narrative script walking through all 8 demo scenarios, see the companion document:
**[`demo/walkthrough.md`](file:///home/zabedin/projects/Aegis/demo/walkthrough.md)**.
