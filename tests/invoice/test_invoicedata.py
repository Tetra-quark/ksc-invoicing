import unittest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from kscinvoicing.invoice.invoicedata import LineItem, InvoiceData


class TestLineItem(unittest.TestCase):

    def test_price_calculation(self):
        item = LineItem(description="Test Service", quantity=3, price_per_unit=50.0)
        self.assertEqual(item.price(), 150.0)

    def test_negative_quantity(self):
        with self.assertRaises(ValueError):
            LineItem(description="Test Service", quantity=-2, price_per_unit=50.0)

    def test_zero_quantity(self):
        with self.assertRaises(ValueError):
            LineItem(description="Test Service", quantity=0, price_per_unit=50.0)

    def test_negative_price(self):
        with self.assertRaises(ValueError):
            LineItem(description="Test Service", quantity=3, price_per_unit=-50.0)

    def test_empty_description(self):
        with self.assertRaises(ValueError):
            LineItem(description="", quantity=3, price_per_unit=50.0)

    def test_non_string_description(self):
        with self.assertRaises(ValueError):
            LineItem(description=123, quantity=3, price_per_unit=50.0)


class TestInvoiceData(unittest.TestCase):


    def setUp(self):
        self.line_items = [
            LineItem(description="Service A", quantity=2, price_per_unit=100.0),
            LineItem(description="Product B", quantity=1, price_per_unit=200.0)
        ]
        self.invoice_date = datetime(2023, 9, 4)

        @dataclass
        class Recipient:
            name: str

        self.invoice_data = InvoiceData(
            sender=None,
            recipient=Recipient(name="Bob Recipient"),
            items=self.line_items,
            date=self.invoice_date,
            save_folder=Path("./"),
            discount=50.0,
            tax_rate=0.2
        )

    def test_get_invoice_name(self):
        self.assertEqual("Invoice_0001_Bob-Recipient_2023-09-04", self.invoice_data.get_invoice_name())

    def test_subtotal(self):
        for item in  self.invoice_data.items:
            print(item.description, item.price())
        self.assertEqual(400.0, self.invoice_data.subtotal)

    def test_tax(self):
        # subtotal 400 - discount 50 = 350.
        # 350 * 0.2 tax rate = 70
        self.assertEqual(70.0, self.invoice_data.tax)

    def test_total(self):
        """
        (subtotal - discount) + tax
        350 + 70 = 420
        """
        self.assertEqual(420.0, self.invoice_data.total)

