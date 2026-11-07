"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@meridian/ui";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@meridian/ui";
import { Badge } from "@meridian/ui";

export default function OnboardPage() {
  const [applicantType, setApplicantType] = useState<"INDIVIDUAL" | "BUSINESS">("INDIVIDUAL");
  const [legalName, setLegalName] = useState("Jennifer Clark");
  const [email, setEmail] = useState("jennifer.clark@example.com");
  const [address, setAddress] = useState("456 Elm St, New York, NY 10001");
  const [dob, setDob] = useState("1992-08-20");
  const [docType, setDocType] = useState("PASSPORT");
  const [docNumber, setDocNumber] = useState("P77112233");
  const [expiryDate, setExpiryDate] = useState("2031-10-15");
  const [companyReg, setCompanyReg] = useState("REG-109283");
  const [beneficialOwners, setBeneficialOwners] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [disposition, setDisposition] = useState<any>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate Onboarding Agent Squad evaluation via API
    setTimeout(() => {
      const isExpired = new Date(expiryDate) < new Date();
      const isWatchlist = legalName.toLowerCase().includes("petrov") || legalName.toLowerCase().includes("mendez");

      if (isWatchlist) {
        setDisposition({
          application_id: "app_" + Math.random().toString(36).substring(2, 8),
          risk_rating: "CRITICAL",
          status: "PENDING_HUMAN_REVIEW",
          recommended_action: "REJECT",
          rationale: "Entity matched active OFAC sanctions watchlist. Escalated to compliance officer.",
          defects: ["Watchlist Hit: Matched OFAC SDN List (Score: 0.95)"],
          evidence: [],
        });
      } else if (isExpired) {
        setDisposition({
          application_id: "app_" + Math.random().toString(36).substring(2, 8),
          risk_rating: "HIGH",
          status: "PENDING_HUMAN_REVIEW",
          recommended_action: "ESCALATE_TO_ANALYST",
          rationale: "Identity document expired. Routed to human compliance analyst for manual review.",
          defects: [`Document expired on ${expiryDate}`],
          evidence: ["ID document format valid"],
        });
      } else {
        setDisposition({
          application_id: "app_" + Math.random().toString(36).substring(2, 8),
          risk_rating: "LOW",
          status: "APPROVED",
          recommended_action: "APPROVE",
          rationale: "All documents verified, corporate active status confirmed, and zero watchlist hits.",
          defects: [],
          evidence: [
            `Verified valid ${docType} (${docNumber})`,
            "Clean Sanctions & PEP screening check (0 hits)",
          ],
        });
      }
      setIsSubmitting(false);
    }, 700);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Digital Account Opening & KYC</h1>
        <p className="text-sm text-slate-500 mt-1">
          Instant identity verification and document cross-checking powered by Meridian's Onboarding Agent Squad.
        </p>
      </div>

      {disposition ? (
        <Card className={`border-2 ${
          disposition.status === "APPROVED"
            ? "border-emerald-300 bg-emerald-50/20"
            : "border-amber-300 bg-amber-50/20"
        }`}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">
                  {disposition.status === "APPROVED" ? "Application Approved 🎉" : "Application Under Review ⏳"}
                </CardTitle>
                <CardDescription>
                  Application ID: <code className="font-mono">{disposition.application_id}</code>
                </CardDescription>
              </div>
              <Badge variant={disposition.risk_rating === "LOW" ? "success" : disposition.risk_rating === "HIGH" ? "warning" : "danger"}>
                {disposition.risk_rating} RISK
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2">
              <p className="font-medium text-slate-900">Decision Rationale:</p>
              <p className="text-slate-600 italic text-xs">{disposition.rationale}</p>

              {disposition.defects.length > 0 && (
                <div className="pt-2">
                  <p className="text-xs font-semibold text-rose-600 uppercase">Defects / Flags Identified:</p>
                  <ul className="list-disc pl-5 text-xs text-rose-700 mt-1 space-y-0.5">
                    {disposition.defects.map((d: string, i: number) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                </div>
              )}

              {disposition.evidence.length > 0 && (
                <div className="pt-2">
                  <p className="text-xs font-semibold text-emerald-700 uppercase">Verified Evidence:</p>
                  <ul className="list-disc pl-5 text-xs text-emerald-800 mt-1 space-y-0.5">
                    {disposition.evidence.map((e: string, i: number) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {disposition.status === "APPROVED" ? (
              <p className="text-xs text-slate-500">
                Your deposit account has been registered on the core double-entry ledger. You may now deposit funds and initiate transfers.
              </p>
            ) : (
              <p className="text-xs text-slate-500">
                A maker-checker review ticket has been dispatched to our compliance operations console. An analyst will review the findings shortly.
              </p>
            )}
          </CardContent>
          <CardFooter className="flex justify-between">
            <Button variant="outline" onClick={() => setDisposition(null)}>
              Submit Another Application
            </Button>
            <Link href={disposition.status === "APPROVED" ? "/accounts" : "/"}>
              <Button variant="primary">
                {disposition.status === "APPROVED" ? "Go to Accounts & Ledger" : "Return to Home"}
              </Button>
            </Link>
          </CardFooter>
        </Card>
      ) : (
        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>Application Form</CardTitle>
              <CardDescription>All submitted data is screened against OFAC, PEP, and registry watchlists</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Applicant Category
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setApplicantType("INDIVIDUAL")}
                    className={`p-3 text-sm font-medium rounded-lg border text-center transition-colors ${
                      applicantType === "INDIVIDUAL"
                        ? "border-blue-600 bg-blue-50 text-blue-900"
                        : "border-slate-300 hover:bg-slate-50 text-slate-700"
                    }`}
                  >
                    👤 Individual Retail
                  </button>
                  <button
                    type="button"
                    onClick={() => setApplicantType("BUSINESS")}
                    className={`p-3 text-sm font-medium rounded-lg border text-center transition-colors ${
                      applicantType === "BUSINESS"
                        ? "border-blue-600 bg-blue-50 text-blue-900"
                        : "border-slate-300 hover:bg-slate-50 text-slate-700"
                    }`}
                  >
                    🏢 Commercial Business
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    Full Legal Name
                  </label>
                  <input
                    type="text"
                    required
                    value={legalName}
                    onChange={(e) => setLegalName(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    Declared Address
                  </label>
                  <input
                    type="text"
                    required
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    required
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {applicantType === "BUSINESS" && (
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
                  <p className="text-xs font-bold text-slate-800 uppercase">Commercial Entity Credentials</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-slate-600 mb-1">Registration Number</label>
                      <input
                        type="text"
                        value={companyReg}
                        onChange={(e) => setCompanyReg(e.target.value)}
                        className="w-full rounded border border-slate-300 p-1.5 text-xs font-mono"
                        placeholder="e.g. REG-109283"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-600 mb-1">Beneficial Owners</label>
                      <input
                        type="text"
                        value={beneficialOwners}
                        onChange={(e) => setBeneficialOwners(e.target.value)}
                        className="w-full rounded border border-slate-300 p-1.5 text-xs"
                        placeholder="Comma separated full names"
                      />
                    </div>
                  </div>
                </div>
              )}

              <div className="border-t border-slate-100 pt-4 space-y-3">
                <p className="text-xs font-bold text-slate-800 uppercase">Identity Document Submission</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs text-slate-600 mb-1">Document Type</label>
                    <select
                      value={docType}
                      onChange={(e) => setDocType(e.target.value)}
                      className="w-full rounded border border-slate-300 p-2 text-xs bg-white"
                    >
                      <option value="PASSPORT">Passport</option>
                      <option value="DRIVERS_LICENSE">Driver's License</option>
                      <option value="NATIONAL_ID">National ID Card</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-slate-600 mb-1">Document Number</label>
                    <input
                      type="text"
                      required
                      value={docNumber}
                      onChange={(e) => setDocNumber(e.target.value)}
                      className="w-full rounded border border-slate-300 p-2 text-xs font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-600 mb-1">Expiry Date</label>
                    <input
                      type="date"
                      required
                      value={expiryDate}
                      onChange={(e) => setExpiryDate(e.target.value)}
                      className="w-full rounded border border-slate-300 p-2 text-xs"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between bg-slate-50/50">
              <Link href="/">
                <Button variant="ghost">Cancel</Button>
              </Link>
              <Button variant="primary" disabled={isSubmitting}>
                {isSubmitting ? "Executing KYC Evaluation..." : "Submit Application for Verification"}
              </Button>
            </CardFooter>
          </Card>
        </form>
      )}
    </div>
  );
}
