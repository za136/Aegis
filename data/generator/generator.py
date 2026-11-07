"""Deterministic Synthetic Bank Data Generator with Labeled AML Typologies."""

import enum
import json
import random
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from faker import Faker


class AMLTypology(str, enum.Enum):
    """Known financial crime typologies with ground-truth labels."""
    NONE = "NONE"                          # Legitimate activity
    STRUCTURING = "STRUCTURING"            # Smurfing (transactions just below $10,000 threshold)
    LAYERING = "LAYERING"                  # Rapid hops through intermediate accounts
    RAPID_MOVEMENT = "RAPID_MOVEMENT"      # Sudden influx into dormant account quickly wired out
    SANCTIONS_EVASION = "SANCTIONS_EVASION"# Name permutation matching designated entities


@dataclass
class SyntheticCustomer:
    """Synthetic consumer or business owner profile."""
    id: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: str
    date_of_birth: str
    national_id: str
    address: str
    city: str
    country: str
    customer_type: str  # RETAIL or BUSINESS
    risk_rating: str    # LOW, MEDIUM, HIGH, PEP
    created_at: str


@dataclass
class SyntheticAccount:
    """Synthetic bank deposit or clearing account."""
    id: str
    account_number: str
    owner_id: str
    currency: str
    account_type: str
    initial_balance: float
    current_balance: float
    status: str
    created_at: str


@dataclass
class SyntheticTransaction:
    """Synthetic transaction record with ground-truth AML labels."""
    id: str
    idempotency_key: str
    source_account_number: str
    destination_account_number: str
    amount: float
    currency: str
    description: str
    transaction_type: str
    timestamp: str
    typology: AMLTypology
    is_suspicious: bool
    typology_metadata: Optional[Dict[str, Any]] = None


class SyntheticBankDataGenerator:
    """Deterministic, reproducible synthetic data generator for banking and AML investigations."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

    def generate_customers(self, count: int = 100) -> List[SyntheticCustomer]:
        """Generate deterministic customer identities."""
        customers: List[SyntheticCustomer] = []
        base_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        for i in range(count):
            is_business = (i % 5 == 0)
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            full_name = f"{first_name} {last_name}"
            if is_business:
                full_name = f"{self.fake.company()} {self.fake.company_suffix()}"

            risk = "LOW"
            if i % 20 == 0:
                risk = "HIGH"
            elif i % 50 == 0:
                risk = "PEP"

            cust_time = base_time + timedelta(days=i % 365, hours=(i * 3) % 24)
            cust = SyntheticCustomer(
                id=f"cust_{uuid.UUID(int=self.seed * 10000 + i)}",
                first_name=first_name,
                last_name=last_name,
                full_name=full_name,
                email=self.fake.email(),
                phone=self.fake.phone_number(),
                date_of_birth=self.fake.date_of_birth(minimum_age=18, maximum_age=75).isoformat(),
                national_id=self.fake.ssn(),
                address=self.fake.street_address(),
                city=self.fake.city(),
                country="US",
                customer_type="BUSINESS" if is_business else "RETAIL",
                risk_rating=risk,
                created_at=cust_time.isoformat(),
            )
            customers.append(cust)
        return customers

    def generate_accounts(self, customers: List[SyntheticCustomer]) -> List[SyntheticAccount]:
        """Generate accounts linked to synthetic customers."""
        accounts: List[SyntheticAccount] = []

        for idx, customer in enumerate(customers):
            # Most customers have 1-2 accounts
            num_accounts = 2 if customer.customer_type == "BUSINESS" else 1
            for acc_idx in range(num_accounts):
                account_id = f"acc_{uuid.UUID(int=self.seed * 20000 + idx * 10 + acc_idx)}"
                initial_bal = round(
                    random.uniform(500.0, 25000.0) if customer.customer_type == "RETAIL"
                    else random.uniform(10000.0, 250000.0),
                    2,
                )
                account_number = f"AEGIS{customer.country}{idx:05d}{acc_idx:02d}"
                acc = SyntheticAccount(
                    id=account_id,
                    account_number=account_number,
                    owner_id=customer.id,
                    currency="USD",
                    account_type="CHECKING" if acc_idx == 0 else "SAVINGS",
                    initial_balance=initial_bal,
                    current_balance=initial_bal,
                    status="ACTIVE",
                    created_at=customer.created_at,
                )
                accounts.append(acc)
        return accounts

    def generate_baseline_transactions(
        self, accounts: List[SyntheticAccount], count: int = 1000
    ) -> List[SyntheticTransaction]:
        """Generate benign daily banking activity (payroll, groceries, subscriptions, rent)."""
        transactions: List[SyntheticTransaction] = []
        descriptions = [
            ("Payroll Deposit", 2500.0, 6000.0),
            ("Grocery Market", 35.0, 180.0),
            ("Electric & Water Utility", 80.0, 220.0),
            ("Coffee & Dining", 6.5, 45.0),
            ("E-Commerce Purchase", 15.0, 350.0),
            ("Apartment Rent Payment", 1200.0, 3200.0),
            ("Fuel & Transportation", 30.0, 75.0),
            ("Streaming Subscription", 9.99, 24.99),
        ]

        start_time = datetime(2025, 6, 1, 8, 0, 0, tzinfo=timezone.utc)

        for i in range(count):
            desc_template, min_amt, max_amt = random.choice(descriptions)
            src_acc = random.choice(accounts)
            dst_acc = random.choice(accounts)
            while dst_acc.id == src_acc.id:
                dst_acc = random.choice(accounts)

            amount = round(random.uniform(min_amt, max_amt), 2)
            tx_time = start_time + timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )

            tx = SyntheticTransaction(
                id=f"tx_{uuid.UUID(int=self.seed * 30000 + i)}",
                idempotency_key=f"idem_{self.seed}_{i}",
                source_account_number=src_acc.account_number,
                destination_account_number=dst_acc.account_number,
                amount=amount,
                currency="USD",
                description=f"{desc_template} #{i}",
                transaction_type="INTERNAL_TRANSFER",
                timestamp=tx_time.isoformat(),
                typology=AMLTypology.NONE,
                is_suspicious=False,
            )
            transactions.append(tx)

        return transactions

    def plant_structuring_typology(
        self, target_account: SyntheticAccount, seed_offset: int = 100
    ) -> List[SyntheticTransaction]:
        """Plant a Structuring (Smurfing) typology pattern:

        Deposits multiple cash amounts just under $10,000 (e.g. $9,200, $9,500, $9,800)
        within a 48-hour window from multiple branches/atms to evade CTR reporting.
        """
        structuring_txs: List[SyntheticTransaction] = []
        base_time = datetime(2025, 7, 10, 9, 30, 0, tzinfo=timezone.utc)
        amounts = [9400.00, 9650.00, 9200.00, 9850.00]

        for idx, amt in enumerate(amounts):
            tx_time = base_time + timedelta(hours=idx * 11 + random.randint(1, 4))
            tx = SyntheticTransaction(
                id=f"tx_struct_{seed_offset}_{idx}",
                idempotency_key=f"idem_struct_{seed_offset}_{idx}",
                source_account_number="EXTERNAL_CASH_DEPOSIT",
                destination_account_number=target_account.account_number,
                amount=amt,
                currency="USD",
                description=f"Branch Cash Deposit - Branch #{random.randint(101, 199)}",
                transaction_type="CASH_DEPOSIT",
                timestamp=tx_time.isoformat(),
                typology=AMLTypology.STRUCTURING,
                is_suspicious=True,
                typology_metadata={
                    "case_group": f"STRUCTURING_CASE_{seed_offset}",
                    "threshold_limit_usd": 10000.00,
                    "smurf_count": len(amounts),
                    "total_accumulated_usd": sum(amounts),
                },
            )
            structuring_txs.append(tx)

        # Immediate outbound consolidation wire 6 hours later
        consolidation_time = tx_time + timedelta(hours=6)
        wire_out = SyntheticTransaction(
            id=f"tx_struct_wire_{seed_offset}",
            idempotency_key=f"idem_struct_wire_{seed_offset}",
            source_account_number=target_account.account_number,
            destination_account_number="OFFSHORE_PANAMA_WIRE_001",
            amount=sum(amounts) - 500.00,
            currency="USD",
            description="International Outgoing Wire - Real Estate Holdings Ltd",
            transaction_type="WIRE_TRANSFER",
            timestamp=consolidation_time.isoformat(),
            typology=AMLTypology.STRUCTURING,
            is_suspicious=True,
            typology_metadata={
                "case_group": f"STRUCTURING_CASE_{seed_offset}",
                "phase": "CONSOLIDATION_SWEEP",
            },
        )
        structuring_txs.append(wire_out)
        return structuring_txs

    def plant_layering_typology(
        self,
        origin_account: SyntheticAccount,
        intermediate_accounts: List[SyntheticAccount],
        destination_account_number: str = "OFFSHORE_BVI_8892",
        seed_offset: int = 200,
    ) -> List[SyntheticTransaction]:
        """Plant a Layering typology pattern:

        Large deposit split and routed through 2-3 hops with minimal time-in-account (<2 hours)
        before being bundled and wired to an offshore counterparty.
        """
        layering_txs: List[SyntheticTransaction] = []
        base_time = datetime(2025, 8, 15, 10, 0, 0, tzinfo=timezone.utc)
        initial_amount = 75000.00

        # Step 1: Inflow to origin
        inflow_tx = SyntheticTransaction(
            id=f"tx_layer_in_{seed_offset}",
            idempotency_key=f"idem_layer_in_{seed_offset}",
            source_account_number="EXTERNAL_INVESTOR_FUND",
            destination_account_number=origin_account.account_number,
            amount=initial_amount,
            currency="USD",
            description="Commercial Loan Inflow",
            transaction_type="WIRE_TRANSFER",
            timestamp=base_time.isoformat(),
            typology=AMLTypology.LAYERING,
            is_suspicious=True,
            typology_metadata={"case_group": f"LAYERING_CASE_{seed_offset}", "hop": 0},
        )
        layering_txs.append(inflow_tx)

        # Step 2: Immediate split to intermediates (hop 1)
        curr_time = base_time + timedelta(minutes=45)
        split_amt = round((initial_amount - 1000.00) / len(intermediate_accounts), 2)
        for idx, inter_acc in enumerate(intermediate_accounts):
            hop1 = SyntheticTransaction(
                id=f"tx_layer_hop1_{seed_offset}_{idx}",
                idempotency_key=f"idem_layer_hop1_{seed_offset}_{idx}",
                source_account_number=origin_account.account_number,
                destination_account_number=inter_acc.account_number,
                amount=split_amt,
                currency="USD",
                description=f"Consulting Invoice Payment #{idx+1}",
                transaction_type="INTERNAL_TRANSFER",
                timestamp=curr_time.isoformat(),
                typology=AMLTypology.LAYERING,
                is_suspicious=True,
                typology_metadata={"case_group": f"LAYERING_CASE_{seed_offset}", "hop": 1},
            )
            layering_txs.append(hop1)

        # Step 3: Outflow from intermediates to offshore target (hop 2, within 90 minutes)
        final_time = curr_time + timedelta(minutes=75)
        for idx, inter_acc in enumerate(intermediate_accounts):
            hop2 = SyntheticTransaction(
                id=f"tx_layer_hop2_{seed_offset}_{idx}",
                idempotency_key=f"idem_layer_hop2_{seed_offset}_{idx}",
                source_account_number=inter_acc.account_number,
                destination_account_number=destination_account_number,
                amount=split_amt - 150.00,
                currency="USD",
                description=f"Export Clearing Settlement Ref-{idx+1}",
                transaction_type="WIRE_TRANSFER",
                timestamp=final_time.isoformat(),
                typology=AMLTypology.LAYERING,
                is_suspicious=True,
                typology_metadata={"case_group": f"LAYERING_CASE_{seed_offset}", "hop": 2},
            )
            layering_txs.append(hop2)

        return layering_txs

    def generate_full_dataset(
        self, profile: str = "dev"
    ) -> Dict[str, Any]:
        """Generate a complete labeled dataset ready for seeding and evals."""
        num_customers = 100 if profile == "dev" else 1000
        num_baseline_txs = 1000 if profile == "dev" else 20000

        customers = self.generate_customers(count=num_customers)
        accounts = self.generate_accounts(customers)
        transactions = self.generate_baseline_transactions(accounts, count=num_baseline_txs)

        # Plant AML Typologies for Ground-Truth Golden Evaluation
        structuring_txs = self.plant_structuring_typology(target_account=accounts[2], seed_offset=101)
        transactions.extend(structuring_txs)

        layering_txs = self.plant_layering_typology(
            origin_account=accounts[5],
            intermediate_accounts=[accounts[6], accounts[7]],
            seed_offset=201,
        )
        transactions.extend(layering_txs)

        # Sort transactions chronologically
        transactions.sort(key=lambda t: t.timestamp)

        return {
            "metadata": {
                "profile": profile,
                "seed": self.seed,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_customers": len(customers),
                "total_accounts": len(accounts),
                "total_transactions": len(transactions),
                "suspicious_transactions_count": sum(1 for t in transactions if t.is_suspicious),
            },
            "customers": [asdict(c) for c in customers],
            "accounts": [asdict(a) for a in accounts],
            "transactions": [asdict(t) for t in transactions],
        }
