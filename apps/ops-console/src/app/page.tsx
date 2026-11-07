import Link from "next/link";
import { Button } from "@meridian/ui";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@meridian/ui";
import { Badge } from "@meridian/ui";

export default function OpsDashboard() {
  const kpis = [
    { label: "24h Payment Volume", value: "$1,482,900.00", change: "+12.4% vs yesterday", variant: "neutral" },
    { label: "STP Settlement Rate", value: "98.4%", change: "Within target SLA", variant: "success" },
    { label: "Active Reserved Holds", value: "$41,200.00", change: "14 held instructions", variant: "warning" },
    { label: "Pending Approvals", value: "2", change: "Requires Human-in-the-Loop", variant: "danger" },
  ];

  const agentSquads = [
    {
      name: "Payment Exception Repair",
      model: "gemini-3.8-flash",
      autonomy: "A1 (HITL Approval Required)",
      status: "Idle / Listening",
      recentAction: "Generated repair payload for rejected payment pmt_98f1 (Code: AC04)",
    },
    {
      name: "Financial Crime (Aegis)",
      model: "gemini-3.8-flash",
      autonomy: "A1 (HITL Approval Required)",
      status: "Monitoring Redpanda stream",
      recentAction: "Completed structuring topology scan on batch #1042",
    },
    {
      name: "Onboarding & KYC Screening",
      model: "gemini-3.8-flash",
      autonomy: "A2 (Autonomous with Notification)",
      status: "Active",
      recentAction: "Extracted and verified passport ID for cust_9918",
    },
  ];

  const exceptions = [
    {
      id: "pmt_ex_101",
      amount: "$1,500.00",
      debtor: "Alice Smith",
      code: "AC04",
      reason: "Account Closed at Beneficiary Bank",
      suggestedAction: "Payment Repair Squad proposed routing to secondary IBAN",
      status: "PENDING_APPROVAL",
    },
    {
      id: "pmt_ex_102",
      amount: "$8,500.00",
      debtor: "Meridian Trading LLC",
      code: "AM04",
      reason: "Hold Exceeds Available Balance ($7,100 available)",
      suggestedAction: "Auto-rejection enforced by double-entry ledger invariant",
      status: "REJECTED",
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Operations & Risk Command Center</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time ledger monitoring, autonomous agent squad telemetry, and human-in-the-loop approvals.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/approvals">
            <Button variant="primary">Review Approvals (2)</Button>
          </Link>
          <Link href="/monitor">
            <Button variant="outline">Payment Monitor</Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {kpis.map((kpi, idx) => (
          <div key={idx} className="p-5 rounded-xl border border-slate-800 bg-[#0d1322] shadow-sm">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">{kpi.label}</p>
            <p className="text-2xl font-bold text-white mt-2">{kpi.value}</p>
            <p className="text-xs text-slate-400 mt-1">{kpi.change}</p>
          </div>
        ))}
      </div>

      {/* Active Autonomous Agent Squads */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Autonomous Agent Squads Telemetry</h2>
            <p className="text-xs text-slate-400">All squads operate with bounded autonomy and MCP tool gating</p>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-cyan-400 border border-slate-700">
            Model: Gemini 3.8 Flash
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {agentSquads.map((squad, i) => (
            <div key={i} className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-white">{squad.name}</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              </div>
              <div className="text-xs space-y-1 text-slate-400">
                <p><span className="text-slate-300">Autonomy Ladder:</span> {squad.autonomy}</p>
                <p><span className="text-slate-300">Status:</span> {squad.status}</p>
              </div>
              <p className="text-xs text-slate-400 italic border-t border-slate-800 pt-2">
                &ldquo;{squad.recentAction}&rdquo;
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Exceptions & Rejections Queue */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Payment Exceptions & Repair Proposals</h2>
            <p className="text-xs text-slate-400">ISO 20022 exception codes under active agent diagnosis</p>
          </div>
          <Link href="/monitor">
            <span className="text-xs font-semibold text-cyan-400 hover:text-cyan-300">
              View All &rarr;
            </span>
          </Link>
        </div>

        <div className="divide-y divide-slate-800">
          {exceptions.map((ex) => (
            <div key={ex.id} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-semibold text-white">{ex.id}</span>
                  <span className="font-semibold text-sm text-slate-200">{ex.amount}</span>
                  <Badge variant="danger">{ex.code}</Badge>
                </div>
                <p className="text-xs text-rose-300/80 mt-1 font-medium">{ex.reason}</p>
                <p className="text-xs text-slate-400 mt-0.5">Debtor: {ex.debtor} &bull; {ex.suggestedAction}</p>
              </div>
              <div>
                <Link href="/approvals">
                  <Button variant="secondary" size="sm">Inspect Action</Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
