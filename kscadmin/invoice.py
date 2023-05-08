from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from decimal import Decimal
import json


@dataclass
class LineItem:
    description: str
    quantity: int
    price_per_unit: Decimal

    def price(self) -> Decimal:
        return self.quantity * self.price_per_unit


def lineitem_from_dict(item: dict) -> LineItem:
    return LineItem(**item)


@dataclass
class Invoice:
    """Class containing invoice information"""
    items: list[LineItem]
    discount: Decimal = field(init=False, repr=False, default=Decimal("0"))
    tax: Decimal = field(init=False, repr=False, default=Decimal("0"))

    invoice_number: str
    date: datetime = datetime.now()
    due_date: Optional[datetime] = None

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


@dataclass
class InvoiceLogger:

    log_path: str

    @property
    def invoice_number(self):
        # TODO seperate invoice logging from the invoice class... pass invoice number to the invoice class.
        """Get next invoice number by incrementing last invoice number from log file by one.
        Or if not found it is first invoice."""
        try:
            with open(self.log_path, 'r') as log:
                d = json.load(log)
                prev_no = max([int(key) for key in d.keys()])
                invoice_number = f"{prev_no + 1:04}"
        except FileNotFoundError:
            # TODO not a safe way to handle this.. file could be not found for many reasons..
            invoice_number = "0001"

        return invoice_number

    def log_invoice(self, date: datetime, sender: str, recipient: str, total: str):

        new_log = {
            "date": date.strftime("%d/%m/%Y"),
            "invoice_from": sender,
            "invoice_to": recipient,
            "total amount": str(total)
        }

        try:
            with open(self.log_path, 'r') as log:
                logdata = json.load(log)
        except FileNotFoundError:
            logdata = {}

        logdata[self.invoice_number] = new_log

        with open(self.log_path, 'w') as log:
            json.dump(logdata, log,
                      indent=4,
                      separators=(',', ': '))

        print("Logfile written to json")

    @staticmethod
    def generate_invoice_name(invoice_id: str, recipient_name: str, date: datetime):
        return f"Invoice_{invoice_id}_{recipient_name.replace(' ', '-')}_{date.strftime('%Y-%m-%d')}"
