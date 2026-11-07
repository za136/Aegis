import { Button } from "@meridian/ui";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@meridian/ui";
import { Badge } from "@meridian/ui";

export default function AccountsPage() {
  const accounts = [
    {
      id: "acc_demo_01",
      account_number: "US12MERI0001001",
      name: "Primary Checking",
      type: "LIABILITY (Customer Deposit)",
      currency: "USD",
      settled_balance: "12,450.00",
      reserved_outgoing: "500.00",
      pending_incoming: "0.00",
      available_balance: "11,950.00",
      status: "ACTIVE",
      created_at: "2026-10-15T08:00:00Z",
    },
    {
      id: "acc_demo_02",
      account_number: "US12MERI0001002",
      name: "High-Yield Savings",
      type: "LIABILITY (Customer Deposit)",
      currency: "USD",
      settled_balance: "45,000.00",
      reserved_outgoing: "0.00",
      pending_incoming: "0.00",
      available_balance: "45,000.00",
      status: "ACTIVE",
      created_at: "2026-10-20T11:30:00Z",
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Accounts & Ledger Balances</h1>
          <p className="text-sm text-slate-500 mt-1">
            Accounts mapped to immutable double-entry journal entries on the Meridian core ledger.
          </p>
        </div>
        <div>
          <Button variant="primary">+ Open New Account</Button>
        </div>
      </div>

      {/* Invariant Explanation Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-xs text-blue-900 flex items-start gap-3">
        <div className="font-bold text-base leading-none">ℹ️</div>
        <div>
          <span className="font-semibold">Core Banking Invariant: </span>
          <span>
            Every account enforces <code>available_balance = settled_balance - reserved_outgoing</code>.
            Settled balances update exclusively via balanced double-entry journal postings where Debits equal Credits.
            Holds guarantee funds cannot be double-spent while a payment undergoes compliance screening.
          </span>
        </div>
      </div>

      {/* Account Cards */}
      <div className="grid grid-cols-1 gap-6">
        {accounts.map((acc) => (
          <Card key={acc.id} className="overflow-hidden">
            <CardHeader className="bg-slate-50/50">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-3">
                    <CardTitle>{acc.name}</CardTitle>
                    <Badge variant="success">{acc.status}</Badge>
                  </div>
                  <p className="text-xs font-mono text-slate-500 mt-1">
                    Account No: {acc.account_number} &bull; Classification: {acc.type}
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-extrabold text-slate-900">${acc.available_balance}</span>
                  <span className="text-xs text-slate-500 ml-1">Available</span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-slate-500">Settled Balance</p>
                  <p className="text-base font-semibold text-slate-800 mt-1">${acc.settled_balance}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-slate-500">Reserved Holds</p>
                  <p className="text-base font-semibold text-amber-600 mt-1">${acc.reserved_outgoing}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-slate-500">Pending Incoming</p>
                  <p className="text-base font-semibold text-emerald-600 mt-1">${acc.pending_incoming}</p>
                </div>
                <div className="p-3 bg-blue-50/60 rounded-lg border border-blue-100">
                  <p className="text-xs text-blue-700 font-medium">Available to Spend</p>
                  <p className="text-base font-bold text-blue-900 mt-1">${acc.available_balance}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
