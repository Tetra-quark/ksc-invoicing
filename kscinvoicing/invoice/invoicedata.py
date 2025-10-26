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

    def __post_init__(self):
        self._validate_quantity()
        self._validate_price_per_unit()
        self._validate_description()

    def _validate_quantity(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
        if not isinstance(self.quantity, int):
            raise ValueError("Quantity must be an integer.")

    def _validate_price_per_unit(self):
        if self.price_per_unit < 0:
            raise ValueError("Price per unit must be a positive number.")
        if not isinstance(self.price_per_unit, Decimal) and not isinstance(self.price_per_unit, float):
            raise ValueError("Price per unit must be a decimal.")

    def _validate_description(self):
        if self.description == "":
            raise ValueError("Description cannot be empty.")
        if not isinstance(self.description, str):
            raise ValueError("Description must be a string.")


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

        self.save_folder = Path(save_folder)
        self.logger = InvoiceLogger(self.save_folder / "log.json")

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
