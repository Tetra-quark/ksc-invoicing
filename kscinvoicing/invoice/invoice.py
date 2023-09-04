from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from decimal import Decimal


@dataclass
class LineItem:
    description: str
    quantity: int
    price_per_unit: Decimal

    def price(self) -> Decimal:
        return self.quantity * self.price_per_unit


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
