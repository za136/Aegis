import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aegis Ops & Compliance Console",
  description: "Agentic Banking Operations, Financial Crime Detection, and Payment Lifecycle Management",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased text-slate-100 bg-[#090d16] min-h-screen">
        <header className="sticky top-0 z-50 bg-[#0d1322]/90 backdrop-blur-md border-b border-slate-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-8">
                <Link href="/" className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-cyan-500/20">
                    🛡️
                  </div>
                  <div>
                    <span className="font-bold text-base tracking-tight text-white">
                      Aegis<span className="text-cyan-400"> / Meridian</span>
                    </span>
                    <span className="text-[10px] text-slate-400 block -mt-1 uppercase tracking-wider font-semibold">
                      Ops & Risk Console
                    </span>
                  </div>
                </Link>
                <nav className="hidden md:flex space-x-6">
                  <Link
                    href="/"
                    className="text-sm font-medium text-slate-300 hover:text-cyan-400 transition-colors"
                  >
                    Overview
                  </Link>
                  <Link
                    href="/monitor"
                    className="text-sm font-medium text-slate-300 hover:text-cyan-400 transition-colors"
                  >
                    Payment Monitor
                  </Link>
                  <Link
                    href="/onboarding"
                    className="text-sm font-medium text-slate-300 hover:text-cyan-400 transition-colors"
                  >
                    Onboarding & KYC
                  </Link>
                  <Link
                    href="/aegis"
                    className="text-sm font-medium text-slate-300 hover:text-cyan-400 transition-colors flex items-center gap-1"
                  >
                    <span>Aegis (AML)</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                  </Link>
                  <Link
                    href="/approvals"
                    className="text-sm font-medium text-slate-300 hover:text-cyan-400 transition-colors flex items-center gap-1.5"
                  >
                    Approvals Queue
                    <span className="inline-flex items-center px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                      4
                    </span>
                  </Link>
                  <Link
                    href="/admin"
                    className="text-sm font-medium text-slate-300 hover:text-cyan-400 transition-colors"
                  >
                    Admin & Governance
                  </Link>
                </nav>
              </div>
              <div className="flex items-center space-x-4">
                <div className="hidden sm:flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-slate-800/80 border border-slate-700 text-slate-300">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                  <span>Gemini 3.8 Flash Squads: Active</span>
                </div>
                <div className="flex items-center space-x-2 pl-4 border-l border-slate-800">
                  <div className="w-8 h-8 rounded-full bg-cyan-900/60 border border-cyan-700 text-cyan-300 font-semibold flex items-center justify-center text-xs">
                    SJ
                  </div>
                  <div className="text-left hidden sm:block">
                    <p className="text-xs font-medium text-white leading-none">Sarah Jenkins</p>
                    <p className="text-[10px] text-cyan-400 leading-none mt-1">Lead Ops Analyst</p>
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
