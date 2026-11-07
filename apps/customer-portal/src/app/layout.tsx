import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Meridian | Customer Banking Portal",
  description: "Next-generation simulated digital banking and payments platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased text-slate-900 bg-slate-50 min-h-screen">
        <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-8">
                <Link href="/" className="flex items-center space-x-2">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
                    M
                  </div>
                  <span className="font-bold text-xl tracking-tight text-slate-900">
                    Meridian<span className="text-blue-600">.bank</span>
                  </span>
                </Link>
                <nav className="hidden md:flex space-x-6">
                  <Link
                    href="/"
                    className="text-sm font-medium text-slate-700 hover:text-blue-600 transition-colors"
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/accounts"
                    className="text-sm font-medium text-slate-700 hover:text-blue-600 transition-colors"
                  >
                    Accounts & Balances
                  </Link>
                  <Link
                    href="/transfer"
                    className="text-sm font-medium text-slate-700 hover:text-blue-600 transition-colors"
                  >
                    Send Money
                  </Link>
                  <Link
                    href="/onboard"
                    className="text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors font-semibold"
                  >
                    Open Account (KYC)
                  </Link>
                </nav>
              </div>
              <div className="flex items-center space-x-4">
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"></span>
                  Live Ledger Connected
                </span>
                <div className="flex items-center space-x-2 pl-4 border-l border-slate-200">
                  <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-semibold flex items-center justify-center text-xs">
                    AS
                  </div>
                  <div className="text-left hidden sm:block">
                    <p className="text-xs font-medium text-slate-900 leading-none">Alice Smith</p>
                    <p className="text-[10px] text-slate-500 leading-none mt-1">alice@example.com</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
