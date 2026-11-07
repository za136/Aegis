/**
 * Strongly-typed API client for Aegis / Meridian Platform.
 */

export type AccountType = "ASSET" | "LIABILITY" | "EQUITY" | "REVENUE" | "EXPENSE";
export type AccountStatus = "PENDING" | "ACTIVE" | "FROZEN" | "RESTRICTED" | "CLOSED";
export type PaymentStatus =
  | "CREATED"
  | "VALIDATED"
  | "SCREENING"
  | "PENDING_APPROVAL"
  | "FUNDS_RESERVED"
  | "SUBMITTED"
  | "SETTLED"
  | "REJECTED"
  | "RETURNED"
  | "FAILED";

export interface Account {
  id: string;
  account_number: string;
  owner_id: string;
  name: string;
  account_type: AccountType;
  currency: string;
  status: AccountStatus;
  settled_balance: string;
  pending_incoming: string;
  reserved_outgoing: string;
  available_balance: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentStateTransition {
  from_status: string;
  to_status: string;
  timestamp: string;
  reason?: string;
}

export interface Payment {
  id: string;
  idempotency_key: string;
  debtor_account_id: string;
  creditor_account_id?: string;
  creditor_account_number: string;
  creditor_name: string;
  amount: string;
  currency: string;
  description: string;
  status: PaymentStatus;
  hold_id?: string;
  journal_entry_id?: string;
  rejection_code?: string;
  rejection_reason?: string;
  state_history: PaymentStateTransition[];
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  roles: string[];
  customer_id?: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export class MeridianClient {
  private baseUrl: string;
  private token?: string;

  constructor(baseUrl: string = "http://localhost:8000/api/v1", token?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.token = token;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`API Error ${response.status}: ${errorBody}`);
    }

    return response.json();
  }

  // Health
  async health(): Promise<{ status: string; service: string }> {
    return this.request("/health");
  }

  // Auth
  async login(email: string, password: string): Promise<AuthTokenResponse> {
    const res = await this.request<AuthTokenResponse>("/auth/token", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe(): Promise<UserProfile> {
    return this.request<UserProfile>("/auth/me");
  }

  // Ledger & Accounts
  async createAccount(data: {
    owner_id: string;
    name: string;
    account_type?: AccountType;
    currency?: string;
  }): Promise<Account> {
    return this.request<Account>("/ledger/accounts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getAccount(accountId: string): Promise<Account> {
    return this.request<Account>(`/ledger/accounts/${accountId}`);
  }

  async getAccountByNumber(accountNumber: string): Promise<Account> {
    return this.request<Account>(`/ledger/accounts/by-number/${accountNumber}`);
  }

  async listAccounts(ownerId: string): Promise<Account[]> {
    return this.request<Account[]>(`/ledger/accounts?owner_id=${encodeURIComponent(ownerId)}`);
  }

  // Payments
  async initiatePayment(data: {
    idempotency_key: string;
    debtor_account_id: string;
    creditor_account_number: string;
    creditor_name: string;
    amount: number;
    currency?: string;
    description: string;
  }): Promise<Payment> {
    return this.request<Payment>("/payments", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getPayment(paymentId: string): Promise<Payment> {
    return this.request<Payment>(`/payments/${paymentId}`);
  }

  async listPayments(options?: {
    debtor_account_id?: string;
    status?: PaymentStatus;
    limit?: number;
  }): Promise<Payment[]> {
    const params = new URLSearchParams();
    if (options?.debtor_account_id) params.set("debtor_account_id", options.debtor_account_id);
    if (options?.status) params.set("status", options.status);
    if (options?.limit) params.set("limit", options.limit.toString());
    const query = params.toString() ? `?${params.toString()}` : "";
    return this.request<Payment[]>(`/payments${query}`);
  }

  async settlePayment(paymentId: string): Promise<Payment> {
    return this.request<Payment>(`/payments/${paymentId}/settle`, {
      method: "POST",
    });
  }

  async rejectPayment(paymentId: string, code: string = "AC04", reason: string = "Account closed"): Promise<Payment> {
    return this.request<Payment>(
      `/payments/${paymentId}/reject?code=${encodeURIComponent(code)}&reason=${encodeURIComponent(reason)}`,
      { method: "POST" }
    );
  }

  // --- Onboarding & KYC Squad ---
  async applyOnboarding(data: {
    applicant_type: "INDIVIDUAL" | "BUSINESS";
    legal_name: string;
    email: string;
    declared_address: string;
    declared_dob?: string;
    business_registration_number?: string;
    declared_beneficial_owners?: string[];
    documents?: Array<{
      doc_type: string;
      document_number: string;
      raw_content: string;
      expiry_date?: string;
      holder_name?: string;
    }>;
  }): Promise<any> {
    return this.request("/onboarding/apply", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getOnboardingApplication(applicationId: string): Promise<any> {
    return this.request(`/onboarding/applications/${applicationId}`);
  }

  async screenEntity(name: string, threshold: number = 0.8): Promise<any[]> {
    return this.request(`/onboarding/screen?name=${encodeURIComponent(name)}&threshold=${threshold}`);
  }

  // --- Approvals Inbox (HITL Maker-Checker) ---
  async listApprovals(status?: string): Promise<any[]> {
    const query = status ? `?status=${status}` : "";
    return this.request(`/approvals${query}`);
  }

  async approveTicket(ticketId: string, reviewedBy: string = "analyst"): Promise<any> {
    return this.request(`/approvals/${ticketId}/approve`, {
      method: "POST",
      body: JSON.stringify({ reviewed_by: reviewedBy }),
    });
  }

  async rejectTicket(ticketId: string, reason: string, reviewedBy: string = "analyst"): Promise<any> {
    return this.request(`/approvals/${ticketId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason, reviewed_by: reviewedBy }),
    });
  }

  // --- Aegis Financial Crime Investigation Squad ---
  async investigateAlert(alertId: string): Promise<any> {
    return this.request(`/aegis/investigate/${alertId}`, {
      method: "POST",
    });
  }

  async getAegisCase(caseId: string): Promise<any> {
    return this.request(`/aegis/cases/${caseId}`);
  }

  async searchAmlPolicies(query: string, topK: number = 3): Promise<any[]> {
    return this.request(`/aegis/policies?query=${encodeURIComponent(query)}&top_k=${topK}`);
  }

  async scanGuardrails(text: string): Promise<{ is_hostile: boolean; detected_patterns: string[]; status: string }> {
    return this.request(`/aegis/scan-guardrails`, {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }
}
