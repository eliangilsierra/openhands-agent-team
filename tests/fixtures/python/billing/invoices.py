"""Invoice totals."""


class InvoiceError(ValueError):
    """Raised for invalid invoices."""


def invoice_total(lines: list[float]) -> float:
    if any(line < 0 for line in lines):
        raise InvoiceError("negative line")
    return sum(lines)
