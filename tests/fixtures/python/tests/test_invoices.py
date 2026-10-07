from billing.invoices import invoice_total


def test_invoice_total() -> None:
    assert invoice_total([1.0, 2.0]) == 3.0
