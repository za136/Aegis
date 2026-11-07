"use client";

import { useState } from "react";
import { Button } from "@meridian/ui";
import { Badge } from "@meridian/ui";

interface SquadConfig {
  name: string;
  label: string;
  model: string;
  enabled: boolean;
  autonomy: "A0" | "A1" | "A2" | "A3";
  description: string;
}

export default function AdminControlPage() {
  const [globalStop, setGlobalStop] = useState(false);
  const [stopReason, setStopReason] = useState("");
  const [transferLimit, setTransferLimit] = useState("100.00");
  const [repairLimit, setRepairLimit] = useState("250.00");
  const [creditLimit, setCreditLimit] = useState("50.00");
  const [saveMessage, setSaveMessage] = useState("");

  const [squads, setSquads] = useState<SquadConfig[]>([
    {
      name: "payment_repair",
      label: "Payment Exception Repair Squad",
      model: "Google Gemini 3.8 Flash",
      enabled: true,
      autonomy: "A2",
      description: "Diagnoses ISO 20022 rejections (AC04, BE05) and patches routing.",
    },
    {
      name: "onboarding",
      label: "Onboarding & KYC Squad",
      model: "Google Gemini 3.8 Flash",
      enabled: true,
      autonomy: "A2",
      description: "Extracts passports/IDs, detects defects, and screens OFAC watchlists.",
    },
    {
      name: "aegis",
      label: "Aegis Financial Crime Squad",
      model: "Google Gemini 3.8 Flash",
      enabled: true,
      autonomy: "A1",
      description: "Analyzes structuring/rapid movement; drafts and adversarially verifies SARs.",
    },
    {
      name: "reconciliation",
      label: "B2B Invoice Reconciliation Squad",
      model: "Google Gemini 3.8 Flash",
      enabled: true,
      autonomy: "A2",
      description: "Multi-pass matcher for remittances, split payments, and ledger credits.",
    },
    {
      name: "support_disputes",
      label: "Customer Support & Disputes Squad",
      model: "Google Gemini 3.8 Flash",
      enabled: true,
      autonomy: "A1",
      description: "Enforces CFPB Regulation E (12 CFR § 1005) and provisional credit rules.",
    },
    {
      name: "ops_copilot",
      label: "Operations Copilot Squad",
      model: "Google Gemini 3.8 Flash",
      enabled: true,
      autonomy: "A2",
      description: "Read-only assistant answering operator questions with grounded citations.",
    },
  ]);

  const [auditLogs, setAuditLogs] = useState([
    {
      time: "2026-11-07 10:14:02 UTC",
      operator: "op_risk_officer",
      action: "AUTONOMY_CLAMP",
      target: "aegis",
      details: "Enforced A1 mandatory human sign-off for all FinCEN SAR filings.",
    },
    {
      time: "2026-11-07 09:30:15 UTC",
      operator: "op_compliance_head",
      action: "UPDATE_LIMIT",
      target: "repair_auto_threshold_usd",
      details: "Set autonomous repair threshold to $250.00.",
    },
  ]);

  const toggleGlobalStop = () => {
    const nextState = !globalStop;
    setGlobalStop(nextState);
    const reason = nextState ? "Manual emergency stop triggered via Ops Admin Console." : "Emergency stop cleared.";
    setStopReason(nextState ? reason : "");
    
    setAuditLogs([
      {
        time: new Date().toISOString(),
        operator: "op_console_admin",
        action: nextState ? "ENGAGE_GLOBAL_STOP" : "DISENGAGE_GLOBAL_STOP",
        target: "ALL_SQUADS",
        details: reason,
      },
      ...auditLogs,
    ]);
  };

  const toggleSquad = (name: string) => {
    setSquads(squads.map(s => {
      if (s.name === name) {
        const nextEnabled = !s.enabled;
        setAuditLogs([
          {
            time: new Date().toISOString(),
            operator: "op_console_admin",
            action: nextEnabled ? "ENABLE_SQUAD" : "DISABLE_SQUAD",
            target: name,
            details: `Squad state changed to enabled=${nextEnabled}.`,
          },
          ...auditLogs,
        ]);
        return { ...s, enabled: nextEnabled };
      }
      return s;
    }));
  };

  const changeAutonomy = (name: string, level: "A0" | "A1" | "A2" | "A3") => {
    setSquads(squads.map(s => {
      if (s.name === name) {
        setAuditLogs([
          {
            time: new Date().toISOString(),
            operator: "op_console_admin",
            action: "CHANGE_AUTONOMY_CEILING",
            target: name,
            details: `Autonomy level adjusted to ${level}.`,
          },
          ...auditLogs,
        ]);
        return { ...s, autonomy: level };
      }
      return s;
    }));
  };

  const saveFinancialLimits = () => {
    setSaveMessage("Financial autonomy thresholds updated successfully!");
    setAuditLogs([
      {
        time: new Date().toISOString(),
        operator: "op_console_admin",
        action: "UPDATE_FINANCIAL_LIMITS",
        target: "gateway_thresholds",
        details: `Transfer: $${transferLimit}, Repair: $${repairLimit}, Provisional: $${creditLimit}`,
      },
      ...auditLogs,
    ]);
    setTimeout(() => setSaveMessage(""), 4000);
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Platform Admin & Autonomy Governance
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Emergency kill switches, dynamic autonomy ceilings, and live governance controls for Google Gemini squads.
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center space-x-3">
          <Badge variant={globalStop ? "destructive" : "outline"} className={globalStop ? "bg-red-600 text-white animate-pulse" : "border-emerald-500 text-emerald-700 bg-emerald-50"}>
            {globalStop ? "SYSTEM HALTED: EMERGENCY STOP ACTIVE" : "ALL AGENT PLATFORM GATES NORMAL"}
          </Badge>
        </div>
      </div>

      {/* Global Emergency Stop Card */}
      <div className={`p-6 rounded-xl border ${globalStop ? "bg-red-50 border-red-300" : "bg-white border-slate-200"} shadow-sm transition-colors`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 flex items-center space-x-2">
              <span className="text-xl">🛑</span>
              <span>Global Emergency Kill Switch</span>
            </h2>
            <p className="text-sm text-slate-600 mt-1">
              Engaging this switch instantly halts all autonomous tool executions, saga actions, and API write invocations across all squads.
            </p>
            {stopReason && (
              <p className="text-xs text-red-700 font-medium mt-2 bg-red-100 p-2 rounded">
                Reason: {stopReason}
              </p>
            )}
          </div>
          <div>
            <button
              onClick={toggleGlobalStop}
              className={`px-5 py-2.5 rounded-lg text-sm font-semibold shadow transition-all ${
                globalStop
                  ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                  : "bg-red-600 hover:bg-red-700 text-white"
              }`}
            >
              {globalStop ? "Disengage Emergency Stop" : "ENGAGE EMERGENCY STOP"}
            </button>
          </div>
        </div>
      </div>

      {/* Per-Squad Governance Matrix */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">
            Agent Squad Autonomy & Activation Matrix
          </h2>
          <span className="text-xs text-slate-500">
            Runtime enforcement via Bounded Tool Gateway
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 uppercase text-xs font-semibold">
              <tr>
                <th className="px-6 py-3">Squad Name</th>
                <th className="px-6 py-3">Primary LLM</th>
                <th className="px-6 py-3">Execution State</th>
                <th className="px-6 py-3">Autonomy Ceiling</th>
                <th className="px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {squads.map((squad) => (
                <tr key={squad.name} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-900">{squad.label}</div>
                    <div className="text-xs text-slate-500">{squad.description}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                      {squad.model}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {squad.enabled ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                        ● ACTIVE
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-50 text-red-700 border border-red-200">
                        ■ PAUSED
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <select
                      value={squad.autonomy}
                      onChange={(e) => changeAutonomy(squad.name, e.target.value as any)}
                      className="text-xs border rounded-md px-2 py-1 bg-white font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="A0">A0 (Suggest Only)</option>
                      <option value="A1">A1 (Act with Human Approval)</option>
                      <option value="A2">A2 (Act within Limits)</option>
                      <option value="A3">A3 (Fully Autonomous)</option>
                    </select>
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => toggleSquad(squad.name)}
                      className={`text-xs font-medium px-3 py-1 rounded transition-colors ${
                        squad.enabled
                          ? "bg-slate-100 hover:bg-slate-200 text-slate-700"
                          : "bg-emerald-100 hover:bg-emerald-200 text-emerald-800"
                      }`}
                    >
                      {squad.enabled ? "Pause Squad" : "Resume Squad"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dynamic Financial Limits Controls */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-2">
          Dynamic Financial Autonomy Limits (A2 Tier)
        </h2>
        <p className="text-sm text-slate-500 mb-6">
          Transactions exceeding these values are automatically escalated to A1 Maker-Checker tickets in the Approvals Inbox.
        </p>

        {saveMessage && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-lg font-medium">
            {saveMessage}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-2">
              Max Autonomous Transfer Limit (USD)
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 text-sm">$</span>
              <input
                type="number"
                value={transferLimit}
                onChange={(e) => setTransferLimit(e.target.value)}
                className="w-full pl-7 pr-3 py-2 border rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <p className="text-xs text-slate-400 mt-1">Default: $100.00</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-2">
              Payment Repair Auto Threshold (USD)
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 text-sm">$</span>
              <input
                type="number"
                value={repairLimit}
                onChange={(e) => setRepairLimit(e.target.value)}
                className="w-full pl-7 pr-3 py-2 border rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <p className="text-xs text-slate-400 mt-1">Default: $250.00</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-2">
              Provisional Credit Auto Threshold (USD)
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 text-sm">$</span>
              <input
                type="number"
                value={creditLimit}
                onChange={(e) => setCreditLimit(e.target.value)}
                className="w-full pl-7 pr-3 py-2 border rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <p className="text-xs text-slate-400 mt-1">Default: $50.00</p>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={saveFinancialLimits}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium shadow"
          >
            Apply Financial Limits
          </button>
        </div>
      </div>

      {/* Governance Audit Log */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-4">
          Administrative Governance Audit Trail
        </h2>
        <div className="space-y-3">
          {auditLogs.map((log, idx) => (
            <div key={idx} className="flex items-start justify-between text-xs p-3 bg-slate-50 rounded-lg border border-slate-100">
              <div>
                <span className="font-semibold text-slate-900 uppercase">[{log.action}]</span>
                <span className="text-slate-600 ml-2">Target: <code className="bg-slate-200 px-1 py-0.5 rounded text-slate-800">{log.target}</code></span>
                <p className="text-slate-700 mt-1 font-mono">{log.details}</p>
              </div>
              <div className="text-right text-slate-400 whitespace-nowrap ml-4">
                <div>{log.operator}</div>
                <div>{log.time}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
