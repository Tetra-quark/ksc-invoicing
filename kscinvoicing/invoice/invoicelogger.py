from dataclasses import dataclass, field
from pathlib import Path

from kscinvoicing.invoice.invoice_store import init_db, get_next_invoice_number
import kscinvoicing.invoice.invoice_store as invoice_store


@dataclass
class InvoiceLogger:

    db_path: Path
    _invoice_number: str = field(init=False, repr=True)

    def __post_init__(self):
        init_db(self.db_path)
        self.invoice_number = get_next_invoice_number(self.db_path)

    @property
    def invoice_number(self):
        return self._invoice_number

    @invoice_number.setter
    def invoice_number(self, number: str):
        self._invoice_number = number

    def log_invoice(self, invoice_data):
        invoice_store.log_invoice(invoice_data, db_path=self.db_path)
        print(f"Invoice {invoice_data.invoice_number} logged to database.")
