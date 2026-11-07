"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@meridian/ui";
import { Badge } from "@meridian/ui";

export default function AegisAMLPage() {
  const [selectedCaseId, setSelectedCaseId] = useState("case_aegis_88192");

  const cases = [
    {
      id: "case_aegis_88192",
      alert_id: "alt_struct_001",
      customer: "Johnathan Doe (cust_john_doe)",
      account: "US12MERI0009988",
      typology: "STRUCTURING",
      priority: "HIGH",
      status: "PENDING_APPROVAL",
      amount_total: "$28,500.00 USD",
      step_budget: "4 / 5 steps used",
      findings: [
        {
          id: "EVID-STRUCT-01",
          title: "Smurfing under $10,000 threshold",
          detail: "3 incoming transfers of $9,500, $9,800, and $9,200 within 28 hours, followed by $28,000 offshore wire.",
        },
      ],
      policies: [
        {
          id: "EVID-POL-5324",
          section: "31 U.S.C. § 5324 / 31 CFR § 1010.314",
          citation: "FinCEN Anti-Structuring Provisions",
        },
      ],
      narrative:
        "Between November 5 and November 6, 2026, account US12MERI0009988 engaged in a pattern of 3 consecutive deposit transactions each strictly under $10,000, totaling $28,500.00 USD [EVID-STRUCT-01].\n\nFollowing the accumulation of structured funds, a consolidating wire transfer was initiated to an offshore entity [EVID-STRUCT-01].\n\nThis observed pattern violates anti-structuring provisions under 31 U.S.C. § 5324, which prohibits conducting transactions designed to evade FinCEN Currency Transaction Reporting [EVID-POL-5324].",
      verifier_status: "PASS",
      verifier_notes: "100% of factual assertions verified against evidence store (2 of 2 citations confirmed).",
    },
    {
      id: "case_aegis_44102",
      alert_id: "alt_rapid_002",
      customer: "Meridian FastFlow Ltd (cust_fast_flow)",
      account: "US12MERI0005544",
      typology: "RAPID_MOVEMENT",
      priority: "HIGH",
      status: "PENDING_APPROVAL",
      amount_total: "$45,000.00 USD",
      step_budget: "3 / 5 steps used",
      findings: [
        {
          id: "EVID-RAPID-01",
          title: "In-and-Out Conduit Movement",
          detail: "$45,000 deposited and $44,900 withdrawn within 1.2 hours with zero ending retention.",
        },
      ],
      policies: [
        {
          id: "EVID-POL-RAPID",
          section: "FATF Recommendation 16",
          citation: "Wire Transfer Conduit and Rapid Movement Rules",
        },
      ],
      narrative:
        "On November 6, 2026, account US12MERI0005544 received an incoming transfer of $45,000.00 USD followed by an immediate outward dispatch of $44,900.00 USD within 1.2 hours [EVID-RAPID-01].\n\nThe account served purely as a temporary conduit with near-zero retained balance, exhibiting high-risk characteristics under FATF Recommendation 16 [EVID-POL-RAPID].",
      verifier_status: "PASS",
      verifier_notes: "All claims verified against transaction timestamps and latency logs.",
    },
  ];

  const activeCase = cases.find((c) => c.id === selectedCaseId) || cases[0];

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Aegis Financial Crime Investigation & SAR Workbench
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-950/80 text-cyan-400 border border-cyan-800">
              Gemini 3.8 Flash Multi-Agent
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Automated graph traversal, FinCEN/FATF Policy RAG, and SAR narratives with strict adversarial verification.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/approvals">
            <Button variant="primary">Review MLRO Approvals Queue</Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-5">
        <div className="p-5 rounded-xl border border-slate-800 bg-[#0d1322]">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Active Typologies</p>
          <p className="text-2xl font-bold text-white mt-1">3 Detected</p>
          <p className="text-xs text-slate-400 mt-0.5">Structuring & Rapid Flow</p>
        </div>
        <div className="p-5 rounded-xl border border-slate-800 bg-[#0d1322]">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Adversarial Verifier Pass</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">100%</p>
          <p className="text-xs text-slate-400 mt-0.5">Zero unevidenced claims</p>
        </div>
        <div className="p-5 rounded-xl border border-slate-800 bg-[#0d1322]">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">SAR Recommendations</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">2 Pending</p>
          <p className="text-xs text-slate-400 mt-0.5">A1 Maker-Checker required</p>
        </div>
        <div className="p-5 rounded-xl border border-slate-800 bg-[#0d1322]">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Neutralized Injections</p>
          <p className="text-2xl font-bold text-cyan-400 mt-1">1 Blocked</p>
          <p className="text-xs text-slate-400 mt-0.5">Hostile memo sanitized</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Case List Sidebar */}
        <div className="space-y-4">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Investigation Cases</p>
          <div className="space-y-3">
            {cases.map((c) => (
              <div
                key={c.id}
                onClick={() => setSelectedCaseId(c.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  selectedCaseId === c.id
                    ? "border-cyan-500 bg-slate-900/90 shadow-md shadow-cyan-950/50"
                    : "border-slate-800 bg-[#0d1322] hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-white">{c.id}</span>
                  <Badge variant={c.typology === "STRUCTURING" ? "warning" : "info"}>
                    {c.typology}
                  </Badge>
                </div>
                <p className="text-sm font-semibold text-slate-200 mt-2">{c.customer}</p>
                <p className="text-xs text-slate-400 font-mono mt-0.5">{c.account}</p>
                <div className="flex justify-between items-center text-xs text-slate-400 mt-3 pt-2 border-t border-slate-800">
                  <span className="font-bold text-white">{c.amount_total}</span>
                  <span>{c.step_budget}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Case Dossier Main View */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-lg font-bold text-white">{activeCase.id}</span>
                  <Badge variant="warning">{activeCase.typology}</Badge>
                  <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800 px-2 py-0.5 rounded">
                    Priority: {activeCase.priority}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Target Account: <span className="font-mono text-slate-200">{activeCase.account}</span> &bull; Alert ID: {activeCase.alert_id}
                </p>
              </div>
              <div className="text-right">
                <span className="text-2xl font-extrabold text-white">{activeCase.amount_total}</span>
              </div>
            </div>

            {/* Pattern Findings & Policy RAG */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
                <p className="font-bold uppercase text-slate-400 text-[10px]">Identified Pattern Findings</p>
                {activeCase.findings.map((f, i) => (
                  <div key={i} className="space-y-1">
                    <span className="font-mono text-amber-400 font-semibold">[{f.id}]</span>
                    <p className="font-semibold text-slate-200">{f.title}</p>
                    <p className="text-slate-400">{f.detail}</p>
                  </div>
                ))}
              </div>

              <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
                <p className="font-bold uppercase text-slate-400 text-[10px]">Statutory Policy Citations (RAG)</p>
                {activeCase.policies.map((p, i) => (
                  <div key={i} className="space-y-1">
                    <span className="font-mono text-emerald-400 font-semibold">[{p.id}]</span>
                    <p className="font-semibold text-slate-200">{p.section}</p>
                    <p className="text-slate-400">{p.citation}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Generated SAR Narrative */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-bold uppercase text-slate-400 tracking-wider">
                  Formal SAR Narrative (Mandatory Evidence Citations)
                </p>
                <span className="text-[10px] text-slate-500 font-mono">Drafter: Gemini 3.8 Flash</span>
              </div>
              <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 font-mono text-xs text-slate-200 whitespace-pre-line leading-relaxed">
                {activeCase.narrative}
              </div>
            </div>

            {/* Adversarial Verifier Stamp */}
            <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-base">🛡️</span>
                  <p className="text-xs font-bold uppercase text-emerald-400 tracking-wider">
                    Adversarial Verifier Audit: PASS
                  </p>
                </div>
                <Badge variant="success">EVIDENCE BACKED</Badge>
              </div>
              <p className="text-xs text-emerald-300 italic">{activeCase.verifier_notes}</p>
            </div>

            {/* Maker-Checker Escalation Action */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-slate-800">
              <div className="text-xs text-slate-400">
                Action requires <span className="text-amber-400 font-semibold">A1 Maker-Checker sign-off</span> from the Lead Compliance Officer.
              </div>
              <Link href="/approvals">
                <Button variant="primary">Authorize SAR Filing via Gateway &rarr;</Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
