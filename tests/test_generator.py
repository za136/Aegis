"""Unit tests for the Deterministic Synthetic Bank Data Generator."""

from data.generator.generator import AMLTypology, SyntheticBankDataGenerator


def test_generator_deterministic_reproducibility():
    """Test that two generators with the identical seed produce identical datasets."""
    gen1 = SyntheticBankDataGenerator(seed=1337)
    gen2 = SyntheticBankDataGenerator(seed=1337)

    cust1 = gen1.generate_customers(count=10)
    cust2 = gen2.generate_customers(count=10)

    assert len(cust1) == len(cust2) == 10
    for c1, c2 in zip(cust1, cust2):
        assert c1.id == c2.id
        assert c1.full_name == c2.full_name
        assert c1.national_id == c2.national_id
        assert c1.customer_type == c2.customer_type


def test_generator_planted_aml_typologies():
    """Test that synthetic dataset contains labeled ground-truth AML typologies."""
    gen = SyntheticBankDataGenerator(seed=99)
    dataset = gen.generate_full_dataset(profile="dev")

    metadata = dataset["metadata"]
    assert metadata["profile"] == "dev"
    assert metadata["total_customers"] == 100
    assert metadata["total_transactions"] > 1000
    assert metadata["suspicious_transactions_count"] > 0

    # Verify presence of both structuring and layering typologies
    typologies = {t["typology"] for t in dataset["transactions"]}
    assert AMLTypology.STRUCTURING.value in typologies
    assert AMLTypology.LAYERING.value in typologies

    # Verify structuring transactions are labeled suspicious
    structuring_txs = [
        t for t in dataset["transactions"] if t["typology"] == AMLTypology.STRUCTURING.value
    ]
    assert len(structuring_txs) >= 4
    for tx in structuring_txs:
        assert tx["is_suspicious"] is True
        assert tx["typology_metadata"] is not None
        assert "case_group" in tx["typology_metadata"]
