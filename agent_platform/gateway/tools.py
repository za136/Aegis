"""Registered banking and investigation tools for agent squads."""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agent_platform.gateway.models import AutonomyLevel
from agent_platform.gateway.registry import register_tool

# In-memory mock counterparty directory for testing and verification
MOCK_COUNTERPARTY_DIRECTORY = {
    "Delta Logistics": {
        "verified_account_number": "US33WELL9988222",
        "routing_status": "ACTIVE",
        "country": "US",
        "aliases": ["Delta Logistics LLC", "Delta Transport"],
    },
    "Acme Global Logistics": {
        "verified_account_number": "US99BOFA8822001",
        "routing_status": "ACTIVE",
        "country": "US",
        "aliases": ["Acme Global", "Acme Logistics"],
    },
    "TechSupplies Corp": {
        "verified_account_number": "US12MERI0002001",
        "routing_status": "ACTIVE",
        "country": "US",
        "aliases": ["Tech Supplies", "TechSupplies Inc"],
    },
}

# In-memory payment repository for testing tool invocations
MOCK_PAYMENT_STORE: Dict[str, Dict[str, Any]] = {
    "pmt_ex_101": {
        "id": "pmt_ex_101",
        "debtor_account": "US12MERI0001001",
        "creditor_account_number": "US33WELL9988111",
        "creditor_name": "Delta Logistics",
        "amount": "1500.00",
        "currency": "USD",
        "status": "REJECTED",
        "rejection_code": "AC04",
        "rejection_reason": "Account Closed at Beneficiary Bank",
    },
    "pmt_valid_01": {
        "id": "pmt_valid_01",
        "debtor_account": "US12MERI0001001",
        "creditor_account_number": "US99BOFA8822001",
        "creditor_name": "Acme Global Logistics",
        "amount": "250.00",
        "currency": "USD",
        "status": "FUNDS_RESERVED",
    },
}


class PaymentDetailsArgs(BaseModel):
    payment_id: str = Field(..., description="Unique ID of the payment instruction")


@register_tool(
    name="get_payment_details",
    description="Retrieve payment instruction metadata, status machine history, and failure codes.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["payment_repair", "financial_crime", "ops_analyst"],
    schema_model=PaymentDetailsArgs,
)
def get_payment_details(payment_id: str) -> Dict[str, Any]:
    payment = MOCK_PAYMENT_STORE.get(payment_id)
    if not payment:
        return {"error": f"Payment {payment_id} not found"}
    return payment


class CounterpartyLookupArgs(BaseModel):
    name: str = Field(..., description="Name of the counterparty or organization to search")


@register_tool(
    name="lookup_counterparty_directory",
    description="Search verified banking counterparty directory for active account numbers and routing details.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["payment_repair", "financial_crime", "onboarding"],
    schema_model=CounterpartyLookupArgs,
)
def lookup_counterparty_directory(name: str) -> Dict[str, Any]:
    for cp_name, data in MOCK_COUNTERPARTY_DIRECTORY.items():
        if cp_name.lower() in name.lower() or any(a.lower() in name.lower() for a in data["aliases"]):
            return {"found": True, "counterparty": cp_name, **data}
    return {"found": False, "query": name, "message": "No verified directory record found."}


class PaymentRepairArgs(BaseModel):
    payment_id: str = Field(..., description="ID of the rejected/stuck payment to repair")
    corrected_account_number: str = Field(..., description="Repaired or verified account number")
    corrected_creditor_name: Optional[str] = Field(None, description="Corrected creditor name")
    repair_reason: str = Field(..., description="Justification and evidence for the repair")


@register_tool(
    name="propose_payment_repair",
    description="Submit a repair proposal for a rejected payment. Subject to A1 human-in-the-loop review.",
    autonomy_level=AutonomyLevel.A1_ACT_WITH_APPROVAL,
    is_write=True,
    required_squad_roles=["payment_repair"],
    schema_model=PaymentRepairArgs,
)
def propose_payment_repair(
    payment_id: str,
    corrected_account_number: str,
    repair_reason: str,
    corrected_creditor_name: Optional[str] = None,
) -> Dict[str, Any]:
    payment = MOCK_PAYMENT_STORE.get(payment_id)
    if not payment:
        return {"success": False, "error": f"Payment {payment_id} not found"}

    # Apply repair
    payment["creditor_account_number"] = corrected_account_number
    if corrected_creditor_name:
        payment["creditor_name"] = corrected_creditor_name
    payment["status"] = "VALIDATED"
    payment["repair_applied"] = {
        "reason": repair_reason,
        "corrected_account_number": corrected_account_number,
    }
    return {
        "success": True,
        "payment_id": payment_id,
        "status": "VALIDATED",
        "message": f"Payment {payment_id} successfully updated with repaired account details.",
    }
