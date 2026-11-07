"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@meridian/ui";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@meridian/ui";
import { Badge } from "@meridian/ui";

export default function TransferPage() {
  const [amount, setAmount] = useState("250.00");
  const [creditorAccount, setCreditorAccount] = useState("US99BOFA8822001");
  const [creditorName, setCreditorName] = useState("Acme Global Logistics");
  const [description, setDescription] = useState("Consulting services invoice #1042");
  const [idempotencyKey, setIdempotencyKey] = useState("idem_tx_9f81a7b2-3c4d");
  const [submittedPayment, setSubmittedPayment] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSendPayment = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate API call to POST /api/v1/payments
    setTimeout(() => {
      setSubmittedPayment({
        id: "pmt_" + Math.random().toString(36).substring(2, 9),
        idempotency_key: idempotencyKey,
        amount: amount,
        currency: "USD",
        debtor_account: "US12MERI0001001",
        creditor_name: creditorName,
        creditor_account: creditorAccount,
        status: "FUNDS_RESERVED",
        hold_id: "hold_res_" + Math.random().toString(36).substring(2, 8),
        message: "Funds successfully reserved on double-entry ledger. Screening saga initiated.",
      });
      setIsSubmitting(false);
    }, 600);
  };

  const regenerateKey = () => {
    setIdempotencyKey("idem_tx_" + Math.random().toString(36).substring(2, 10));
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Send Payment</h1>
        <p className="text-sm text-slate-500 mt-1">
          Initiate an atomic fund transfer executed through Meridian's payment lifecycle saga.
        </p>
      </div>

      {submittedPayment ? (
        <Card className="border-emerald-200 bg-emerald-50/30">
          <CardHeader>
            <div className="flex items-center gap-2">
              <span className="text-2xl">✅</span>
              <div>
                <CardTitle className="text-emerald-900">Transfer Initiated & Reserved</CardTitle>
                <CardDescription className="text-emerald-700">
                  Payment instruction dispatched to the core ledger engine.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="bg-white p-4 rounded-lg border border-emerald-200/80 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">Payment ID:</span>
                <span className="font-mono font-semibold">{submittedPayment.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Hold ID (Two-Phase Lock):</span>
                <span className="font-mono text-amber-700 font-semibold">{submittedPayment.hold_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Amount Reserved:</span>
                <span className="font-bold text-slate-900">${submittedPayment.amount} USD</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Status:</span>
                <Badge variant="warning">{submittedPayment.status}</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Idempotency Key:</span>
                <span className="font-mono text-xs">{submittedPayment.idempotency_key}</span>
              </div>
            </div>

            <p className="text-xs text-slate-500">
              The two-phase commit has reserved your funds on the double-entry ledger. Settlement will finalize automatically upon sanctions/compliance screening clearance.
            </p>
          </CardContent>
          <CardFooter className="flex justify-between">
            <Button
              variant="outline"
              onClick={() => {
                setSubmittedPayment(null);
                regenerateKey();
              }}
            >
              Send Another Transfer
            </Button>
            <Link href="/">
              <Button variant="primary">Return to Dashboard</Button>
            </Link>
          </CardFooter>
        </Card>
      ) : (
        <form onSubmit={handleSendPayment}>
          <Card>
            <CardHeader>
              <CardTitle>Transfer Instruction</CardTitle>
              <CardDescription>All transfers are protected by two-phase holds and idempotency controls</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Source Account
                </label>
                <select className="w-full rounded-lg border-slate-300 border p-2.5 text-sm bg-white focus:ring-2 focus:ring-blue-500">
                  <option value="acc_demo_01">
                    Primary Checking (US12MERI0001001) - Available: $11,950.00 USD
                  </option>
                  <option value="acc_demo_02">
                    High-Yield Savings (US12MERI0001002) - Available: $45,000.00 USD
                  </option>
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    Beneficiary Account No. / IBAN
                  </label>
                  <input
                    type="text"
                    required
                    value={creditorAccount}
                    onChange={(e) => setCreditorAccount(e.target.value)}
                    className="w-full rounded-lg border-slate-300 border p-2 text-sm focus:ring-2 focus:ring-blue-500 font-mono"
                    placeholder="US..."
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    Beneficiary Name
                  </label>
                  <input
                    type="text"
                    required
                    value={creditorName}
                    onChange={(e) => setCreditorName(e.target.value)}
                    className="w-full rounded-lg border-slate-300 border p-2 text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="Individual or Company Name"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Transfer Amount (USD)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400 font-bold">
                    $
                  </span>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full pl-8 rounded-lg border-slate-300 border p-2 text-lg font-bold text-slate-900 focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Payment Reference / Memo
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-lg border-slate-300 border p-2 text-sm focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. Invoice payment, rent, vendor"
                />
              </div>

              <div className="pt-2 border-t border-slate-100">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>Idempotency Key: <code className="font-mono text-slate-700">{idempotencyKey}</code></span>
                  <button
                    type="button"
                    onClick={regenerateKey}
                    className="text-blue-600 hover:text-blue-800 underline font-medium"
                  >
                    Regenerate
                  </button>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between bg-slate-50/50">
              <Link href="/">
                <Button variant="ghost">Cancel</Button>
              </Link>
              <Button variant="primary" disabled={isSubmitting}>
                {isSubmitting ? "Reserving Funds on Ledger..." : `Submit Payment ($${amount})`}
              </Button>
            </CardFooter>
          </Card>
        </form>
      )}
    </div>
  );
}
