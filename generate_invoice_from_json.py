"""
Main script to create invoices. Parameters provided by json file, see template for examples.
"""
from pathlib import Path
from datetime import datetime
import json
from decimal import Decimal
import argparse

from kscinvoicing.info import Address, CompanySender, IndividualRecipient, CompanyRecipient
from kscinvoicing.invoice import LineItem, InvoiceData, InvoiceLogger
from kscinvoicing.pdf.borbinvoice import BorbInvoice
from kscinvoicing.pdf.invoicebuilder import build_invoice


def invoice_data_from_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data


def extract_sender_from_json(data: dict) -> CompanySender:
    sender = CompanySender(
        siren=data['sender']['siren'],
        company_name=data['sender']['company'],
        name=data['sender']['name'],
        address=Address(**data['sender']['address']),
        email=data['sender']['email'],
        phone=data['sender']['phone'],
        website=data['sender']['website'],
    )
    return sender


def extract_recipient_from_json(data: dict) -> IndividualRecipient | CompanyRecipient:
    recipient = IndividualRecipient(
        name=data['recipient']['name'],
        address=Address(**data['recipient']['address']),
        email=data['recipient']['email'],
        phone=data['recipient']['phone'],
    )
    return recipient


def extract_lineitems_from_json(data: dict) -> list[LineItem]:
    items = []
    for item in data['lineitem_details']:
        items.append(LineItem(description=item['description'],
                              quantity=item['quantity'],
                              price_per_unit=Decimal(item['price_per_unit'])
                              ))
    return items


def generate_invoice(data: dict) -> BorbInvoice:
    """
    Generate pdf invoice from provided invoice data dictionary.
    """

    invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d')

    # create invoice
    invoice = InvoiceData(
        sender=extract_sender_from_json(data),
        recipient=extract_recipient_from_json(data),
        items=extract_lineitems_from_json(data),
        date=invoice_date,
        save_folder=Path(data['save_location']),
    )

    invoice_with_pdf = build_invoice(
        invoice=invoice,
        logopath=data['logo_path'],
        footer_text=data['footer_text'],
    )

    return invoice_with_pdf


def main():

    parser = argparse.ArgumentParser(description="Generate invoice from json file.")
    parser.add_argument("filepath", type=str, help="path to json file")
    parser.add_argument("--no-preview", action='store_false', help="open generated draft invoice in default pdf viewer")
    args = parser.parse_args()

    data = invoice_data_from_json(args.filepath)

    invoice_with_pdf = generate_invoice(data)

    show_preview = args.no_preview # slightly confusing name
    if show_preview:
        invoice_with_pdf.preview_with_optional_save()
    else:
        invoice_with_pdf.save()


if __name__ == '__main__':
    main()
