import { Button } from "@meridian/ui";
import { Badge } from "@meridian/ui";

export default function PaymentMonitorPage() {
  const payments = [
    {
      id: "pmt_8829a1",
      idempotency_key: "idem_tx_9f81a7b2-3c4d",
      debtor_account: "US12MERI0001001 (Alice Smith)",
      creditor_account: "US99BOFA8822001 (Acme Global Logistics)",
      amount: "250.00",
      currency: "USD",
      status: "FUNDS_RESERVED",
      hold_id: "hold_9f81-01",
      journal_entry_id: null,
      state_history: [
        { from: "NONE", to: "CREATED", time: "10:14:02 UTC", reason: "Payment received via API Gateway" },
        { from: "CREATED", to: "VALIDATED", time: "10:14:03 UTC", reason: "Account active & balance invariant passed" },
        { from: "VALIDATED", to: "SCREENING", time: "10:14:03 UTC", reason: "Dispatched to Sanctions Screening" },
        { from: "SCREENING", to: "FUNDS_RESERVED", time: "10:14:04 UTC", reason: "Two-phase hold placed on ledger" },
      ],
    },
    {
      id: "pmt_7712c9",
      idempotency_key: "idem_tx_1234abcd-7788",
      debtor_account: "US12MERI0001001 (Alice Smith)",
      creditor_account: "US12MERI0002001 (Bob Vance)",
      amount: "150.00",
      currency: "USD",
      status: "SETTLED",
      hold_id: "hold_7712-00 (Captured)",
      journal_entry_id: "je_settle_88192",
      state_history: [
        { from: "NONE", to: "CREATED", time: "Yesterday, 15:30:00 UTC", reason: "Payment created" },
        { from: "CREATED", to: "VALIDATED", time: "Yesterday, 15:30:01 UTC", reason: "Validation passed" },
        { from: "VALIDATED", to: "FUNDS_RESERVED", time: "Yesterday, 15:30:02 UTC", reason: "Hold placed" },
        { from: "FUNDS_RESERVED", to: "SETTLED", time: "Yesterday, 15:30:04 UTC", reason: "Double-entry settlement postings executed" },
      ],
    },
    {
      id: "pmt_ex_101",
      idempotency_key: "idem_tx_fail_9981",
      debtor_account: "US12MERI0001001 (Alice Smith)",
      creditor_account: "US33WELL9988111 (Delta Logistics)",
      amount: "1,500.00",
      currency: "USD",
      status: "REJECTED",
      hold_id: "hold_ex101 (Released)",
      journal_entry_id: null,
      rejection_code: "AC04",
      rejection_reason: "Account Closed at Beneficiary Bank",
      state_history: [
        { from: "NONE", to: "CREATED", time: "Nov 5, 09:12:00 UTC", reason: "Payment created" },
        { from: "CREATED", to: "FUNDS_RESERVED", time: "Nov 5, 09:12:01 UTC", reason: "Hold placed" },
        { from: "FUNDS_RESERVED", to: "REJECTED", time: "Nov 5, 09:12:05 UTC", reason: "Rejection response AC04 received. Hold released." },
      ],
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Payment Lifecycle & Ledger Monitor</h1>
        <p className="text-sm text-slate-400 mt-1">
          End-to-end saga tracking from instruction submission to two-phase hold reservation and double-entry settlement.
        </p>
      </div>

      <div className="space-y-6">
        {payments.map((pmt) => (
          <div key={pmt.id} className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-base font-bold text-white">{pmt.id}</span>
                  <Badge
                    variant={
                      pmt.status === "SETTLED"
                        ? "success"
                        : pmt.status === "FUNDS_RESERVED"
                        ? "warning"
                        : "danger"
                    }
                  >
                    {pmt.status}
                  </Badge>
                  {pmt.rejection_code && (
                    <span className="text-xs font-mono font-semibold text-rose-400 bg-rose-950/50 border border-rose-800 px-2 py-0.5 rounded">
                      Code: {pmt.rejection_code}
                    </span>
                  )}
                </div>
                <p className="text-xs font-mono text-slate-400 mt-1">
                  Idempotency Key: {pmt.idempotency_key}
                </p>
              </div>
              <div className="text-right">
                <span className="text-2xl font-extrabold text-white">${pmt.amount}</span>
                <span className="text-xs text-slate-400 ml-1">{pmt.currency}</span>
              </div>
            </div>

            {/* Parties & Ledger References */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
              <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800/80">
                <p className="text-slate-400 font-medium">Debtor Account</p>
                <p className="font-mono text-slate-200 mt-1 truncate">{pmt.debtor_account}</p>
              </div>
              <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800/80">
                <p className="text-slate-400 font-medium">Creditor Account</p>
                <p className="font-mono text-slate-200 mt-1 truncate">{pmt.creditor_account}</p>
              </div>
              <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800/80">
                <p className="text-slate-400 font-medium">Ledger Hold ID</p>
                <p className="font-mono text-amber-400 mt-1">{pmt.hold_id || "None"}</p>
              </div>
              <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800/80">
                <p className="text-slate-400 font-medium">Journal Entry ID</p>
                <p className="font-mono text-emerald-400 mt-1">{pmt.journal_entry_id || "Pending Settlement"}</p>
              </div>
            </div>

            {/* Saga State History Timeline */}
            <div className="pt-2">
              <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Saga State Machine Transitions
              </p>
              <div className="relative pl-6 space-y-3 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                {pmt.state_history.map((step, idx) => (
                  <div key={idx} className="relative text-xs">
                    <span className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-cyan-500 ring-4 ring-[#0d1322]"></span>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                      <span className="font-semibold text-slate-200">
                        {step.from} &rarr; <span className="text-cyan-400">{step.to}</span>
                      </span>
                      <span className="text-slate-500 font-mono text-[11px]">{step.time}</span>
                    </div>
                    <p className="text-slate-400 mt-0.5">{step.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
