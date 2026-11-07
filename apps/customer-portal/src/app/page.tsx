import Link from "next/link";
import { Button } from "@meridian/ui";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@meridian/ui";
import { Badge } from "@meridian/ui";

export default function CustomerDashboard() {
  // In Phase 1 Walking Skeleton, demo data reflects active ledger and payment states
  const accounts = [
    {
      id: "acc_demo_01",
      account_number: "US12MERI0001001",
      name: "Primary Checking",
      currency: "USD",
      settled_balance: "12,450.00",
      reserved_outgoing: "500.00",
      available_balance: "11,950.00",
      status: "ACTIVE",
    },
    {
      id: "acc_demo_02",
      account_number: "US12MERI0001002",
      name: "High-Yield Savings",
      currency: "USD",
      settled_balance: "45,000.00",
      reserved_outgoing: "0.00",
      available_balance: "45,000.00",
      status: "ACTIVE",
    },
  ];

  const recentPayments = [
    {
      id: "pmt_01",
      creditor: "TechSupplies Corp",
      account: "US99BOFA8822001",
      amount: "500.00",
      status: "FUNDS_RESERVED",
      statusVariant: "warning" as const,
      timestamp: "Today, 10:14 AM",
    },
    {
      id: "pmt_02",
      creditor: "Bob Vance",
      account: "US12MERI0002001",
      amount: "150.00",
      status: "SETTLED",
      statusVariant: "success" as const,
      timestamp: "Yesterday, 3:30 PM",
    },
    {
      id: "pmt_03",
      creditor: "Acme Cloud Services",
      account: "US44CHAS9911002",
      amount: "1,200.00",
      status: "SETTLED",
      statusVariant: "success" as const,
      timestamp: "Nov 4, 2026",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Welcome back, Alice</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time balance across your accounts backed by Meridian's double-entry core ledger.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/transfer">
            <Button variant="primary">Send Money</Button>
          </Link>
          <Link href="/accounts">
            <Button variant="outline">View All Accounts</Button>
          </Link>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-l-4 border-l-blue-600">
          <CardHeader>
            <CardDescription>Total Available Balance</CardDescription>
            <CardTitle className="text-3xl font-extrabold text-slate-900 mt-1">$56,950.00</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-500">Immediate funds ready for transfer or withdrawal</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-slate-400">
          <CardHeader>
            <CardDescription>Total Settled Balance</CardDescription>
            <CardTitle className="text-3xl font-bold text-slate-800 mt-1">$57,450.00</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-500">Total ledger posted funds</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardHeader>
            <CardDescription>Pending Reserved Holds</CardDescription>
            <CardTitle className="text-3xl font-bold text-amber-600 mt-1">$500.00</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-500">1 outbound payment currently in screening saga</p>
          </CardContent>
        </Card>
      </div>

      {/* Accounts List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Your Accounts</CardTitle>
              <CardDescription>Deposit liability accounts on the core ledger</CardDescription>
            </div>
            <Link href="/accounts">
              <span className="text-xs font-semibold text-blue-600 hover:text-blue-800">
                Manage Accounts &rarr;
              </span>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-slate-100">
            {accounts.map((acc) => (
              <div key={acc.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900">{acc.name}</span>
                    <Badge variant="success">{acc.status}</Badge>
                  </div>
                  <p className="text-xs font-mono text-slate-500 mt-0.5">{acc.account_number}</p>
                </div>
                <div className="sm:text-right">
                  <p className="text-lg font-bold text-slate-900">${acc.available_balance} <span className="text-xs font-normal text-slate-500">{acc.currency}</span></p>
                  <p className="text-xs text-slate-400">
                    Settled: ${acc.settled_balance} | Holds: ${acc.reserved_outgoing}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Payment Activity</CardTitle>
              <CardDescription>State transitions through the two-phase saga coordinator</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-slate-100">
            {recentPayments.map((pmt) => (
              <div key={pmt.id} className="py-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-900">{pmt.creditor}</p>
                  <p className="text-xs text-slate-500 font-mono">{pmt.account} &bull; {pmt.timestamp}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-slate-900">-${pmt.amount}</p>
                  <div className="mt-1">
                    <Badge variant={pmt.statusVariant}>{pmt.status}</Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
