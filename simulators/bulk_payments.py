"""Bulk Payment Batch Simulator & Processor (ISO 20022 pacs.008 & NACHA ACH)."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.payments.models import PaymentInstruction, PaymentStatus
from services.payments.saga import payment_saga
from services.common.telemetry import metrics, tracer


class BulkPaymentItem(BaseModel):
    end_to_end_id: str
    debtor_account_id: str
    creditor_account_id: str
    creditor_name: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "USD"
    remittance_info: str = "Payroll / Vendor Disbursement"


class BulkPaymentBatch(BaseModel):
    batch_id: str
    batch_reference: str
    format: str = "ISO20022_PACS_008"  # or NACHA_ACH
    debtor_company_id: str
    total_instructions: int
    total_batch_volume: Decimal
    items: List[BulkPaymentItem]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BatchProcessingSummary(BaseModel):
    batch_id: str
    total_processed: int
    settled_count: int
    failed_count: int
    total_settled_volume: str
    total_failed_volume: str
    failed_payment_ids: List[str] = Field(default_factory=list)
    iso20022_xml_sample: Optional[str] = None
    execution_duration_ms: float = 0.0


class BulkPaymentProcessor:
    """Enterprise batch payment generator and execution engine."""

    @staticmethod
    def generate_iso20022_pacs008_xml(batch: BulkPaymentBatch) -> str:
        """Generate ISO 20022 pacs.008.001.10 customer credit transfer XML envelope."""
        now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.10">',
            '  <FIToFICstmrCdtTrf>',
            '    <GrpHdr>',
            f'      <MsgId>MSG-{batch.batch_id}</MsgId>',
            f'      <CreDtTm>{now_str}</CreDtTm>',
            f'      <NbOfTxs>{batch.total_instructions}</NbOfTxs>',
            f'      <TtlIntrBkSttlmAmt Ccy="USD">{batch.total_batch_volume}</TtlIntrBkSttlmAmt>',
            '    </GrpHdr>',
        ]

        for item in batch.items:
            xml_lines.extend([
                '    <CdtTrfTxInf>',
                '      <PmtId>',
                f'        <EndToEndId>{item.end_to_end_id}</EndToEndId>',
                '      </PmtId>',
                f'      <IntrBkSttlmAmt Ccy="{item.currency}">{item.amount}</IntrBkSttlmAmt>',
                '      <Dbtr>',
                f'        <Nm>{batch.debtor_company_id}</Nm>',
                '      </Dbtr>',
                '      <DbtrAcct>',
                f'        <Id><Othr><Id>{item.debtor_account_id}</Id></Othr></Id>',
                '      </DbtrAcct>',
                '      <Cdtr>',
                f'        <Nm>{item.creditor_name}</Nm>',
                '      </Cdtr>',
                '      <CdtrAcct>',
                f'        <Id><Othr><Id>{item.creditor_account_id}</Id></Othr></Id>',
                '      </CdtrAcct>',
                '      <RmtInf>',
                f'        <Ustrd>{item.remittance_info}</Ustrd>',
                '      </RmtInf>',
                '    </CdtTrfTxInf>',
            ])

        xml_lines.extend([
            '  </FIToFICstmrCdtTrf>',
            '</Document>',
        ])
        return "\n".join(xml_lines)

    @classmethod
    async def process_batch(cls, batch: BulkPaymentBatch) -> BatchProcessingSummary:
        """Process all instructions in the batch through the two-phase hold & payment saga."""
        start_time = datetime.utcnow()
        settled_count = 0
        failed_count = 0
        settled_vol = Decimal("0.00")
        failed_vol = Decimal("0.00")
        failed_ids: List[str] = []

        with tracer.start_span("bulk_batch_execution", batch_id=batch.batch_id, count=batch.total_instructions):
            for item in batch.items:
                instruction = PaymentInstruction(
                    payment_id=f"pay_bulk_{uuid.uuid4().hex[:8]}",
                    source_account_id=item.debtor_account_id,
                    destination_account_id=item.creditor_account_id,
                    amount=item.amount,
                    currency=item.currency,
                    reference=f"{item.end_to_end_id} - {item.remittance_info}",
                    status=PaymentStatus.PENDING,
                )

                result = await payment_saga.execute_payment(instruction)
                if result.status == PaymentStatus.SETTLED:
                    settled_count += 1
                    settled_vol += item.amount
                    metrics.payments_processed.inc(1, channel="bulk_batch", status="settled")
                    metrics.holds_reserved.inc(1, channel="bulk_batch")
                else:
                    failed_count += 1
                    failed_vol += item.amount
                    failed_ids.append(instruction.payment_id)
                    metrics.payments_processed.inc(1, channel="bulk_batch", status="failed")

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000.0
            xml_sample = cls.generate_iso20022_pacs008_xml(batch)

            return BatchProcessingSummary(
                batch_id=batch.batch_id,
                total_processed=len(batch.items),
                settled_count=settled_count,
                failed_count=failed_count,
                total_settled_volume=str(settled_vol),
                total_failed_volume=str(failed_vol),
                failed_payment_ids=failed_ids,
                iso20022_xml_sample=xml_sample,
                execution_duration_ms=round(duration, 2),
            )


bulk_processor = BulkPaymentProcessor()
