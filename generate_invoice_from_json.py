"""
Main script to create invoices. Parameters provided by json file, see template for examples.
"""
import platform
from pathlib import Path
from datetime import datetime
import subprocess  # for pdf show
import json
from decimal import Decimal
import argparse

from kscinvoicing.info.address import Address
from kscinvoicing.info.contactinfo import ContactInfo
from kscinvoicing.invoice import LineItem, Invoice, InvoiceLogger
from kscinvoicing.pdf.invoicebuilder import save_document, build_invoice


def invoice_data_from_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data


def preview_file(draftpath: Path):
    """
    Open the generated draft invoice in the default PDF viewer based on the OS.
    """
    system = platform.system()
    if system == "Windows":
        subprocess.run(['start', draftpath], shell=True, check=True)
    elif system == "Darwin":  # macOS
        subprocess.run(['open', draftpath], check=True)
    elif system == "Linux":
        subprocess.run(['xdg-open', draftpath], check=True)
    else:
        print(f"Preview unavailable for OS: {system}. Please open the file manually: {draftpath}")


def extract_sender_from_json(data: dict) -> ContactInfo:
    sender = ContactInfo(name=data['sender']['name'],
                         address=Address(**data['sender']['address']),
                         email=data['sender']['email'],
                         phone=data['sender']['phone'],
                         website=data['sender']['website'])
    return sender


def extract_recipient_from_json(data: dict) -> ContactInfo:
    recipient = ContactInfo(name=data['recipient']['name'],
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


def main():

    parser = argparse.ArgumentParser(description="Generate invoice from json file.")
    parser.add_argument("filepath", type=str, help="path to json file")
    parser.add_argument("--no-preview", action='store_false', help="open generated draft invoice in default pdf viewer")
    args = parser.parse_args()

    show_preview = args.no_preview
    data = invoice_data_from_json(args.filepath)


    invoices_path = Path(data['save_location'])
    logger = InvoiceLogger(invoices_path / "log.json")

    invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d')
    sender = extract_sender_from_json(data)
    recipient = extract_recipient_from_json(data)
    items = extract_lineitems_from_json(data)

    # create invoice
    invoice = Invoice(items=items,
                      date=invoice_date,
                      invoice_number=logger.invoice_number)


    pdf_invoice = build_invoice(
        siren_number=data['sender']['siren'],
        company_name=data['sender']['company'],
        sender=sender,
        recipient=recipient,
        invoice=invoice,
        logopath=data['logo_path'],
        footer_text=data['footer_text'],
    )

    invoice_name = invoice.generate_invoice_name(recipient.name)

    save_path = invoices_path / f"{invoice_name}.pdf"
    save_document(save_path, pdf_invoice)

    if show_preview:

        # Save draft and open pdf with Preview
        draftpath = invoices_path / f'DRAFT_{invoice_name}.pdf'
        builder.save_document(draftpath, pdf_invoice)

        preview_file(draftpath)

        response = input("Do you want to save this draft as an official invoice? (type 'y' to save)\n")
        if response == "y":
            savepath = invoices_path / f"{invoice_name}.pdf"
            draftpath.rename(savepath)
            print(f"Draft saved to : '{savepath}'")
            logger.log_invoice(date=invoice.date,
                               sender=sender.name,
                               recipient=recipient.name,
                               total=str(invoice.total))
        else:
            draftpath.unlink()
            print("Draft deleted.")

    else:
        savepath = invoices_path / f"{invoice_name}.pdf"
        builder.save_document(savepath, pdf_invoice)
        logger.log_invoice(date=invoice.date,
                           sender=sender.name,
                           recipient=recipient.name,
                           total=str(invoice.total))



if __name__ == '__main__':
    main()
