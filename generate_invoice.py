"""
Main script to create invoices. Parameters for euro/hour rate, number of hours worked, recipient, invoice date should be set here.
"""
from pathlib import Path
from datetime import datetime
import subprocess  # for pdf show

from kscadmin.address import AddressFactory
from kscadmin.contactinfo import ContactInfo
from kscadmin.invoice import LineItem, Invoice, InvoiceLogger
from kscadmin.invoicebuilder import InvoiceBuilder

from config import personal_details as SENDER
from config import company_details as COMPANY
from config import client_info as CLIENT_BOOK
from config import invoice_items as INVOICE_ITEMS

FOOTER_TEXT = "TVA non applicable - art. 293B du CGI"

LOGO_PATH = '/Users/jeff/Personal/KSC/Logo/Koppanyi-logos 2/Koppanyi-logos_transparent copy.png'
INVOICE_DIRECTORY = '/Users/jeff/Personal/KSC/Invoices/tests'

DATE = datetime(day=1, month=4, year=5000)


# TODO maybe company name should be printed somewhere on the invoice... Currently only present in logo.

def main():
    RECIPIENT = CLIENT_BOOK['BelleFerme']

    # create sender
    address_fac = AddressFactory()
    sender_address = address_fac.create_address_from_str(SENDER['address'])
    sender = ContactInfo(SENDER['fullname'], sender_address, SENDER['email'], SENDER['phone'], SENDER['website'])

    # create recipient
    recipient_address = address_fac.create_address_from_str(RECIPIENT['address'])
    recipient = ContactInfo(RECIPIENT['fullname'], recipient_address, RECIPIENT['email'])

    items = []
    for item in INVOICE_ITEMS:
        items.append(LineItem(**item))

    logpath = f"{INVOICE_DIRECTORY}/log.json"
    logger = InvoiceLogger(logpath)

    # create invoice
    invoice = Invoice(items=items,
                      date=DATE,
                      invoice_number=logger.invoice_number)

    builder = InvoiceBuilder()
    pdf_invoice = builder.build_invoice(COMPANY['SIREN'], sender, recipient, invoice, LOGO_PATH, FOOTER_TEXT)

    invoice_name = logger.generate_invoice_name(logger.invoice_number, recipient.name, invoice.date)

    # Save draft and open pdf with Preview
    draftpath = Path(INVOICE_DIRECTORY) / f'DRAFT_{invoice_name}.pdf'
    builder.save_document(draftpath, pdf_invoice)
    subprocess.run(['open', draftpath], check=True)

    response = input("Do you want to save this draft as an offcial invoice? (type 'yes' to save)\n")
    if response == "yes":
        # Save draft as official invoice
        savepath = INVOICE_DIRECTORY / Path(f"{invoice_name}.pdf")
        draftpath.rename(savepath)
        print(f"Draft saved to : '{savepath}'")
        logger.log_invoice(date=invoice.date,
                           sender=sender.name,
                           recipient=recipient.name,
                           total=str(invoice.total))
    else:
        draftpath.unlink()
        print("Draft deleted.")


if __name__ == '__main__':
    main()
