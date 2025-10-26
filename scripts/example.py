"""
A full example of how to create and preview an invoice using kscinvoicing in python.
"""
from datetime import datetime
from pathlib import Path
from kscinvoicing import (
    Address,
    CompanySender,
    IndividualRecipient,
    LineItem,
    InvoiceData,
    build_invoice,
)

def main():

    logo_path = Path(__file__).parents[1] / "example_config/example_logo.png"

    # Define Sender
    sender = CompanySender(
        siren="123456789",
        company_name="QuBit Technologies",
        name="Alice Sender",
        address=Address(
            number="",
            street="Gower St",
            city="London",
            postcode="WC1E 6BT",
            country="United Kingdom"
        ),
        email="alice@example.com",
        phone="(+33) 0123456789",
        website=None
    )

    # Define Recipient
    recipient = IndividualRecipient(
        name="Bob Recipient",
        address=Address(
            number="386",
            street="Rte de Meyrin",
            city="Meyrin",
            postcode="1217",
            country="Switzerland"
        ),
        phone=None,
        email="bob@example.com",
    )

    items = [
        LineItem(description="service 42", quantity=3, price_per_unit=50.00),
        LineItem(description="product 505", quantity=1, price_per_unit=200.00),
    ]

    invoice_data = InvoiceData(
        sender=sender,
        recipient=recipient,
        items=items,
        date=datetime.now(),
        save_folder="./",
        discount=0.0,
        tax_rate=0.0
    )

    invoice = build_invoice(
        invoice=invoice_data,
        logo_path=logo_path,
        logo_width=200,
        footer_text="Some legal text.",
    )
    invoice.preview_with_optional_save()


if __name__ == '__main__':
    main()
