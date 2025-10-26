from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from decimal import Decimal

from kscinvoicing.info.party import CompanySender, IndividualRecipient
from kscinvoicing.invoice.invoicelogger import InvoiceLogger


@dataclass
class LineItem:
    description: str
    quantity: int
    price_per_unit: Decimal

    def price(self) -> Decimal:
        return self.quantity * self.price_per_unit


class InvoiceData:
    """Class representing all the data for a complete invoice."""

    def __init__(
        self,
        sender: CompanySender,
        recipient: IndividualRecipient,
        items: list[LineItem],
        save_folder: Path,
        date: datetime = datetime.now(),
        due_date: datetime = None,
        discount: Decimal = Decimal("0"),
        tax_rate: Decimal = Decimal("0"),
    ):
        self.sender = sender
        self.recipient = recipient
        self.items = items

        self.save_folder = save_folder
        self.logger = InvoiceLogger(save_folder / "log.json")

        self.date = date
        self.due_date = due_date
        self.invoice_number = self.logger.invoice_number

        self.discount = discount
        self.tax_rate = tax_rate

    def log_invoice(self):
        self.logger.log_invoice(
            date=self.date,
            sender=self.sender.name,
            recipient=self.recipient.name,
            total=str(self.total),
        )

    def get_invoice_name(self):
        return f"Invoice_{self.invoice_number}_{self.recipient.name.replace(' ', '-')}_{self.date.strftime('%Y-%m-%d')}"

    @property
    def subtotal(self) -> Decimal:
        return sum([item.price() for item in self.items])

    @property
    def tax(self) -> Decimal:
        return (self.subtotal - self.discount) * self.tax_rate

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.tax - self.discount

    @staticmethod
    def calculate_discount_from_rate(discount_rate: Decimal, price: Decimal):
        if Decimal("0.00") <= discount_rate <= Decimal('1.00'):
            raise ValueError("Discount rate must be a decimal between 0 and 1.")
        return (1 - discount_rate) * price
