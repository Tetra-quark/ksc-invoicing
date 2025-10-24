from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
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


class Invoice:
    """Class representing a complete invoice."""

    def __init__(self,
                 sender: CompanySender,
                 recipient: IndividualRecipient,
                 items: list[LineItem],
                 logger: InvoiceLogger,
                 date: datetime = datetime.now(),
                 due_date: datetime = None,
                 ):
        self.sender = sender
        self.recipient = recipient
        self.items = items

        self.logger = logger

        self.date = date
        self.due_date = due_date
        self.invoice_number = logger.invoice_number

        # TODO implement tax and discount properly
        self.discount = Decimal("0")
        self.tax = Decimal("0")

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
    def total(self, tax=Decimal('0'), discount=Decimal('0')) -> Decimal:
        # TODO need do double check how tax and discount interacts.
        return self.subtotal + tax - discount

    @staticmethod
    def calculate_tax(tax_rate: Decimal, price_excl_tax: Decimal) -> Decimal:
        return tax_rate * price_excl_tax

    @staticmethod
    def calculate_discount_from_rate(discount_rate: Decimal, price: Decimal):
        # TODO need to check behaviour interaction with taxation..
        if Decimal("0.00") <= discount_rate <= Decimal('1.00'):
            raise ValueError("Discount rate must be a decimal between 0 and 1.")
        return (1 - discount_rate) * price
