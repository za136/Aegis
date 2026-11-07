import Link from "next/link";
import { Button } from "@meridian/ui";
import { Badge } from "@meridian/ui";

export default function OnboardingOpsPage() {
  const cases = [
    {
      id: "app_78a19b",
      type: "INDIVIDUAL",
      legal_name: "Jennifer Clark",
      submitted_at: "Today, 11:20 AM",
      risk_rating: "LOW",
      action: "APPROVED (A2 Autonomous)",
      confidence: "98.0%",
      defects: [],
      evidence: ["Valid US Passport verified", "Clean Sanctions & PEP screening check"],
      ticket_id: null,
    },
    {
      id: "app_33f20c",
      type: "INDIVIDUAL",
      legal_name: "Marcus Aurelius",
      submitted_at: "Today, 10:45 AM",
      risk_rating: "HIGH",
      action: "PENDING_HUMAN_REVIEW (A1 Maker-Checker)",
      confidence: "65.0%",
      defects: ["Document expired on 2021-06-30"],
      evidence: ["Driver's License format valid"],
      ticket_id: "ticket_app_33f20c",
    },
    {
      id: "app_99e81d",
      type: "BUSINESS",
      legal_name: "NorthStar Maritime Holdings Ltd",
      submitted_at: "Yesterday, 16:10 PM",
      risk_rating: "CRITICAL",
      action: "REJECT / ESCALATED (A1 Maker-Checker)",
      confidence: "99.0%",
      defects: ["Watchlist Hit: Matched Viktor Anatolyevich Petrov on OFAC SDN List (Score: 0.95)"],
      evidence: ["Corporate registration active in Cyprus"],
      ticket_id: "ticket_app_99e81d",
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Customer Onboarding & KYC Pipeline
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Autonomous multi-agent document extraction, defect identification, and sanctions/PEP screening.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/approvals">
            <Button variant="primary">Review Pending Tickets</Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="p-5 rounded-xl border border-slate-800 bg-[#0d1322]">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Total Applications</p>
          <p className="text-2xl font-bold text-white mt-1">142</p>
          <p className="text-xs text-slate-400 mt-0.5">Past 24 hours</p>
        </div>
        <div className="p-5 rounded-xl border border-slate-800 bg-[#0d1322]">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">A2 Auto-Approval Rate</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">91.5%</p>
          <p className="text-xs text-slate-400 mt-0.5">Low risk / Clean KYC verification</p>
        </div>
        <div className="p-5 rounded-xl border border-slate-800 bg-[#0d1322]">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Escalated to Maker-Checker</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">8.5%</p>
          <p className="text-xs text-slate-400 mt-0.5">Document defects or watchlist hits</p>
        </div>
      </div>

      {/* Case List */}
      <div className="space-y-4">
        {cases.map((c) => (
          <div key={c.id} className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-base font-bold text-white">{c.id}</span>
                  <span className="font-semibold text-slate-200 text-sm">{c.legal_name}</span>
                  <Badge
                    variant={
                      c.risk_rating === "LOW"
                        ? "success"
                        : c.risk_rating === "HIGH"
                        ? "warning"
                        : "danger"
                    }
                  >
                    {c.risk_rating} RISK
                  </Badge>
                  <span className="text-xs text-slate-400">({c.type})</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Submitted: <span className="font-mono text-slate-300">{c.submitted_at}</span> &bull; Agent Confidence: {c.confidence}
                </p>
              </div>
              <div className="text-right">
                <span className="text-xs font-semibold text-cyan-400 block">{c.action}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 bg-slate-900/60 rounded-lg border border-slate-800 space-y-1.5">
                <p className="font-bold uppercase text-slate-400 text-[10px]">Verified Evidence</p>
                {c.evidence.length > 0 ? (
                  <ul className="list-disc pl-4 text-emerald-400 space-y-0.5">
                    {c.evidence.map((e, idx) => (
                      <li key={idx}>{e}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-500 italic">None verified</p>
                )}
              </div>

              <div className="p-3.5 bg-slate-900/60 rounded-lg border border-slate-800 space-y-1.5">
                <p className="font-bold uppercase text-slate-400 text-[10px]">Identified Defects / Watchlist Hits</p>
                {c.defects.length > 0 ? (
                  <ul className="list-disc pl-4 text-rose-400 space-y-0.5">
                    {c.defects.map((d, idx) => (
                      <li key={idx}>{d}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-emerald-500 font-medium">✓ Zero defects detected</p>
                )}
              </div>
            </div>

            {c.ticket_id && (
              <div className="flex justify-end pt-2">
                <Link href="/approvals">
                  <Button variant="secondary" size="sm">
                    Inspect Ticket in Approvals Queue &rarr;
                  </Button>
                </Link>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
