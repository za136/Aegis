"use client";

import { useState } from "react";
import { Button } from "@meridian/ui";
import { Badge } from "@meridian/ui";

export default function ApprovalsPage() {
  const [items, setItems] = useState([
    {
      id: "appr_rep_01",
      type: "PAYMENT_REPAIR_PROPOSAL",
      payment_id: "pmt_ex_101",
      requester: "Payment Exception Repair Squad (Gemini 3.8 Flash)",
      amount: "$1,500.00 USD",
      autonomy_level: "A1 (Human-in-the-Loop Required)",
      summary: "Repair stuck transfer rejected with code AC04 (Account Closed).",
      details: {
        original_account: "US33WELL9988111",
        proposed_account: "US33WELL9988222",
        beneficiary: "Delta Logistics",
        rationale:
          "Agent analyzed recent successful settlement history for Delta Logistics and matched updated routing profile confirmed in counterparty registry. Replacement verified against checksum rules.",
        confidence: "98.2%",
      },
      status: "PENDING",
    },
    {
      id: "appr_val_02",
      type: "HIGH_VALUE_SETTLEMENT",
      payment_id: "pmt_hv_9901",
      requester: "Corporate Treasury Dispatcher",
      amount: "$250,000.00 USD",
      autonomy_level: "A1 (Policy Threshold: > $100,000)",
      summary: "Maker-checker sign-off required for settlement exceeding autonomous limit.",
      details: {
        original_account: "US12MERI0001001 (Meridian Liquidity Pool)",
        proposed_account: "US99BOFA1100223 (Federal Reserve Bank Nostro)",
        beneficiary: "FRB Clearinghouse",
        rationale: "Routine end-of-day Nostro liquidity replenishment transfer.",
        confidence: "100.0%",
      },
      status: "PENDING",
    },
    {
      id: "appr_kyc_03",
      type: "ONBOARDING_KYC_EXCEPTION",
      payment_id: "app_33f20c",
      requester: "Onboarding & KYC Squad (Gemini 3.8 Flash)",
      amount: "N/A (Account Opening)",
      autonomy_level: "A1 (Document Defect Flagged)",
      summary: "Customer Marcus Aurelius submitted identity document expired on 2021-06-30.",
      details: {
        original_account: "N/A",
        proposed_account: "New Retail Checking",
        beneficiary: "Marcus Aurelius",
        rationale:
          "Extraction agent detected expired Driver's License DL994411. Clean Sanctions/PEP screening check. Compliance officer discretion required to approve or request updated document.",
        confidence: "65.0%",
      },
      status: "PENDING",
    },
    {
      id: "appr_sar_04",
      type: "FINANCIAL_CRIME_SAR_FILING",
      payment_id: "case_aegis_88192",
      requester: "Aegis Financial Crime Squad (Gemini 3.8 Flash)",
      amount: "$28,500.00 USD (Suspicious Volume)",
      autonomy_level: "A1 (Mandatory MLRO Authorization)",
      summary: "Authorize filing of Suspicious Activity Report (SAR) for Structuring / Smurfing activity.",
      details: {
        original_account: "US12MERI0009988 (Johnathan Doe)",
        proposed_account: "FinCEN SAR e-Filing Transmission",
        beneficiary: "Financial Crimes Enforcement Network (FinCEN)",
        rationale:
          "Account engaged in 3 consecutive deposits under $10,000 threshold ($9,500, $9,800, $9,200) followed by immediate offshore wire. Adversarial verifier passed 100% of claims with cited evidence EVID-STRUCT-01 and statutory citation 31 U.S.C. 5324.",
        confidence: "99.4%",
      },
      status: "PENDING",
    },
  ]);

  const handleAction = (id: string, action: "APPROVED" | "REJECTED") => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: action } : item))
    );
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Human-in-the-Loop Approvals Queue
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Review and authorize bounded A1 agent squad proposals and high-value payment instructions.
        </p>
      </div>

      <div className="space-y-6">
        {items.map((item) => (
          <div
            key={item.id}
            className={`rounded-xl border p-6 space-y-5 transition-all ${
              item.status === "APPROVED"
                ? "border-emerald-800 bg-emerald-950/20"
                : item.status === "REJECTED"
                ? "border-rose-800 bg-rose-950/20"
                : "border-slate-800 bg-[#0d1322]"
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-bold text-white">{item.id}</span>
                  <Badge variant={item.status === "APPROVED" ? "success" : item.status === "REJECTED" ? "danger" : "warning"}>
                    {item.status}
                  </Badge>
                  <span className="text-xs font-mono text-amber-400 bg-amber-950/40 border border-amber-800 px-2 py-0.5 rounded">
                    {item.autonomy_level}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Submitted by: <span className="text-slate-200 font-medium">{item.requester}</span>
                </p>
              </div>
              <div className="text-right">
                <span className="text-2xl font-extrabold text-white">{item.amount}</span>
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-sm font-semibold text-slate-200">{item.summary}</p>
              
              <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 space-y-2 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-300">
                  <p><span className="text-slate-400">Target Payment:</span> <code className="font-mono">{item.payment_id}</code></p>
                  <p><span className="text-slate-400">Beneficiary:</span> {item.details.beneficiary}</p>
                  <p><span className="text-slate-400">Original Routing:</span> <code className="font-mono">{item.details.original_account}</code></p>
                  <p><span className="text-slate-400">Proposed Routing:</span> <code className="font-mono text-cyan-400">{item.details.proposed_account}</code></p>
                </div>
                <div className="pt-2 border-t border-slate-800">
                  <p className="text-slate-400 mb-1 font-medium">Agent Reasoning & Evidence (Confidence: {item.details.confidence}):</p>
                  <p className="text-slate-300 italic">{item.details.rationale}</p>
                </div>
              </div>
            </div>

            {item.status === "PENDING" ? (
              <div className="flex items-center justify-end gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={() => handleAction(item.id, "REJECTED")}
                >
                  Reject & Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={() => handleAction(item.id, "APPROVED")}
                >
                  Authorize Execution (via MCP)
                </Button>
              </div>
            ) : (
              <div className="text-right text-xs font-semibold text-slate-400 pt-2">
                Action recorded: <span className="text-white">{item.status}</span> by Sarah Jenkins
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
