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
from kscinvoicing.pdf.invoicebuilder import InvoiceBuilder


def invoice_data_from_json(path: str) -> dict:
    with open(path, "r") as file:
        data = json.load(file)
        return data

def generate_invoice_name(invoice_id: str, recipient_name: str, date: datetime):
    return f"Invoice_{invoice_id}_{recipient_name.replace(' ', '-')}_{date.strftime('%Y-%m-%d')}"


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


def main():

    parser = argparse.ArgumentParser(description="Generate invoice from json file.")
    parser.add_argument("filepath", type=str, help="path to json file")
    parser.add_argument("--no-preview", action='store_false', help="open generated draft invoice in default pdf viewer")
    args = parser.parse_args()

    data = invoice_data_from_json(args.filepath)
    show_preview = args.no_preview

    invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d')

    # create sender
    sender = ContactInfo(name=data['sender']['name'],
                         address=Address(**data['sender']['address']),
                         email=data['sender']['email'],
                         phone=data['sender']['phone'],
                         website=data['sender']['website'])

    # create recipient
    recipient = ContactInfo(name=data['recipient']['name'],
                            address=Address(**data['recipient']['address']),
                            email=data['recipient']['email'],
                            phone=data['recipient']['phone'],
                            )

    items = []
    for item in data['lineitem_details']:
        items.append(LineItem(description=item['description'],
                              quantity=item['quantity'],
                              price_per_unit=Decimal(item['price_per_unit'])
                              ))

    invoices_path = Path(data['save_location'])
    logpath = f"{invoices_path}/log.json"
    logger = InvoiceLogger(logpath)

    # create invoice
    invoice = Invoice(items=items,
                      date=invoice_date,
                      invoice_number=logger.invoice_number)

    builder = InvoiceBuilder()
    pdf_invoice = builder.build_invoice(siren_number=data['sender']['siren'],
                                        company_name=data['sender']['company'],
                                        sender=sender,
                                        recipient=recipient,
                                        invoice=invoice,
                                        logopath=data['logo_path'],
                                        footer_text=data['footer_text'],
                                        )

    invoice_name = generate_invoice_name(logger.invoice_number, recipient.name, invoice.date)

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
