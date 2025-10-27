from math import radians
from pathlib import Path
from datetime import datetime
from typing import Optional
from decimal import Decimal

from borb.pdf.canvas.geometry.rectangle import Rectangle
from borb.pdf import (
    Paragraph,
    Image,
    Alignment,
    FixedColumnWidthTable,
    TableCell,
    Page,
    SingleColumnLayout,
    Document,
)
from PIL import Image as PILImage

from kscinvoicing.info.party import CompanySender, IndividualRecipient, CompanyRecipient
from kscinvoicing.invoice.invoicedata import LineItem, InvoiceData
from kscinvoicing.pdf.borbinvoice import BorbInvoice
from kscinvoicing.pdf.tableschema import TableSchema
from kscinvoicing.pdf.utils import (
    VerticalSpacer,
    format_money_factory,
    STYLE,
    COLOR, Currency, get_headings_for_language, Language,
)


def get_image_dimensions(path) -> tuple[int, int]:
    with PILImage.open(path) as logo_pil:
        return logo_pil.size


def build_invoice(
    invoice: InvoiceData,
    logo_path: str = None,
    logo_width: int = 200,
    footer_text: str = None,
    language: str = "fr",
) -> BorbInvoice:
    """
    Main method to build borb invoice. Returns BorbInvoice object containing borb pdf document and invoice data.
    Args:
        invoice: InvoiceData object containing invoice data.
        logo_path: Path to logo image file.
        logo_width: Width of logo image in pixels.
        footer_text: Optional text to display in footer.
    Returns:
        BorbInvoice object containing borb pdf document and invoice data.
    """
    if logo_path is None:
        logo = None
    elif not Path(logo_path).is_file():
        print(f"Warning: logo file '{logo_path}' not found.")
        logo = None
    else:
        w, h = get_image_dimensions(logo_path)
        logo_height = logo_width * h // w
        logo = Image(Path(logo_path), width=Decimal(logo_width), height=Decimal(logo_height))

    contact_details_schema = _build_contact_details_schema(invoice.sender, invoice.recipient)
    contact_details_table = contact_details_schema.build_table()

    invoice_information_schema = _build_invoice_info_schema(company_name=invoice.sender.company_name,
                                                            siren_number=invoice.sender.siren,
                                                            invoice_number=invoice.invoice_number,
                                                            bill_date=invoice.date,
                                                            due_date=invoice.due_date)
    invoice_information_table = invoice_information_schema.build_table()

    itemised_table = _build_itemised_table(
        line_items=invoice.items,
        currency=Currency(invoice.currency),
        lang=Language(language),
    )

    totals_schema = _build_totals_schema(
        subtotal=invoice.subtotal,
        total=invoice.total,
        discount=invoice.discount,
        tax=invoice.tax,
        currency=Currency(invoice.currency),
    )
    totals_table = totals_schema.build_table()

    pdf = _build_invoice_document(
        logo=logo,
        contact_details_table=contact_details_table,
        invoice_information_table=invoice_information_table,
        itemised_table=itemised_table,
        totals_table=totals_table,
        footer_text=footer_text,
    )
    return BorbInvoice(invoice=invoice, document=pdf)

def _build_invoice_document(
    contact_details_table: FixedColumnWidthTable,
    invoice_information_table: FixedColumnWidthTable,
    itemised_table: FixedColumnWidthTable,
    totals_table: FixedColumnWidthTable,
    footer_text: str = None,
    logo: Image = None,
) -> Document:
    """Creates a pdf object for invoice using borb tables."""
    # Create document & add page
    pdf = Document()
    page = Page()
    pdf.add_page(page)

    # layout
    layout = SingleColumnLayout(page)
    layout.vertical_margin = page.get_page_info().get_height() * Decimal(0.02)

    if logo is not None:
        layout.add(logo)

    layout.add(Paragraph(" "))  # vertical space
    layout.add(contact_details_table)  # Invoice personal & recipient information
    layout.add(VerticalSpacer(size=Decimal('15')))
    layout.add(invoice_information_table)  # Invoice information (date etc, invoice number)
    layout.add(VerticalSpacer(size=Decimal('5')))
    layout.add(itemised_table)  # Invoice items
    layout.add(VerticalSpacer(size=Decimal('10')))
    layout.add(totals_table)  # Invoice totals summary
    if footer_text is not None:
        _add_footer(page, footer_text)

    return pdf


def _add_footer(page: Page, footer_text: str):
    """Places a centered footer at the bottom of the page."""
    ps = page.get_page_info().get_size()
    rect = Rectangle(Decimal(0), Decimal(0), Decimal(ps[0]), Decimal(60))
    footer = Paragraph(footer_text, font_size=Decimal(8), font=STYLE.primary_font, horizontal_alignment=Alignment.CENTERED)
    footer.paint(page, rect)


def _build_invoice_info_schema(company_name: str,
                              siren_number: str,
                              invoice_number: str,
                              bill_date: datetime,
                              due_date: Optional[datetime] = None,
                              ) -> TableSchema:
    """ Inserts a table with the bill number, todays date and optionally the due date."""

    if due_date:
        due_date_label = "Due Date"  # or "Date d'echeance"
        due_date_value = due_date.strftime('%d/%m/%Y')
    else:
        due_date_label = " "
        due_date_value = " "

    # bill information
    tabledata = [[company_name, " ", "Facture Nº", invoice_number],
                 ["SIREN ", siren_number, "Date", bill_date.strftime('%d/%m/%Y')],
                 [" ", " ", due_date_label, due_date_value]]

    column_width_ratios = [Decimal(1), Decimal(5), Decimal(2), Decimal(2)]

    # specify cells to embolden
    bold_cells = [*[(i, 0) for i in range(len(tabledata))], *[(i, 2) for i in range(len(tabledata))]]
    double_cells = [(0, 0)]

    tableschema = TableSchema(tabledata, column_width_ratios, bold_cells, double_cells)

    return tableschema


def _contact_info_to_list(contact: CompanySender | IndividualRecipient) -> list:
    """Put contact info object into a list to be inserted into invoice table."""
    details = [
        contact.name,
        *contact.address.address_lines(),
    ]
    if contact.phone is not None:
        details.append(contact.phone)
    if contact.email is not None:
        details.append(contact.email)
    return details


def _build_contact_details_schema(sender: CompanySender, recipient: IndividualRecipient) -> TableSchema:
    """ Inserts a table with sender and recipient personal information."""

    sender_details = _contact_info_to_list(sender)
    recipient_details = _contact_info_to_list(recipient)

    table_shape = (6, 3)  # (rows, columns)
    tabledata = [[""] * table_shape[1] for _ in range(table_shape[0])]

    tabledata[0][0] = "Facturé par"
    tabledata[0][-1] = "Facturé à"

    for i in range(1, table_shape[0]):

        # sender details in first column
        if len(sender_details):
            tabledata[i][0] = sender_details.pop(0)
        # recipient details in last column
        if len(recipient_details):
            tabledata[i][-1] = recipient_details.pop(0)

    # Bold headings
    bold_cells = [(0, 0), (0, 2)]
    column_width_ratios = [Decimal(2), Decimal(1), Decimal(2)]

    tableschema = TableSchema(tabledata=tabledata,
                              column_widths=column_width_ratios,
                              bold_cells=bold_cells)

    return tableschema


def _build_totals_schema(
        subtotal: Decimal,
        total: Decimal,
        discount: Decimal,
        tax: Decimal,
        currency: Currency,
) -> TableSchema:
    """Builds TableSchema """

    format_money = format_money_factory(currency)

    tabledata = []

    def row_helper(label: str, value: str) -> list[str]:
        return [" ", label, value]

    # don't show totals if unnecessary
    if discount != Decimal('0') or tax != Decimal('0'):
        fmt_subtotal = format_money(subtotal)
        tabledata.append(row_helper("Sous-Total", fmt_subtotal))

        if discount != Decimal('0'):
            fmt_discount = format_money(discount)
            tabledata.append(row_helper("Remise Total", fmt_discount))

        if tax != Decimal('0'):
            fmt_tax = format_money(tax)
            tabledata.append(row_helper("TVA", fmt_tax))

    fmt_total = format_money(total)
    tabledata.append(row_helper("Total", fmt_total))

    bold_cells = [(i, 1) for i in range(len(tabledata))]
    column_width_ratios = [Decimal(4), Decimal(1), Decimal(1)]
    tableschema = TableSchema(tabledata=tabledata,
                              column_widths=column_width_ratios,
                              bold_cells=bold_cells)
    return tableschema


def _build_itemised_table(line_items: list[LineItem], currency: Currency, lang: Language) -> FixedColumnWidthTable:
    """Builds Borb table containing line items for the invoice."""

    format_money = format_money_factory(currency)
    headings = get_headings_for_language(lang)
    assert len(headings) == 4

    def heading_helper(text: str) -> TableCell:
        return TableCell(
            Paragraph(
                text,
                font_color=COLOR['white'],
                font=STYLE.title_font,
                horizontal_alignment=Alignment.LEFT,
                vertical_alignment=Alignment.MIDDLE,
                # padding_top=Decimal(5),
                # padding_left=Decimal(5),
            )
        )

    def row_content_helper(text: str) -> TableCell:
        return TableCell(
            Paragraph(
                text,
                font=STYLE.primary_font,
                respect_newlines_in_text=True,
            ),
        )

    table = FixedColumnWidthTable(
        number_of_rows=len(line_items) + 1,
        number_of_columns=4,
        column_widths=[Decimal(3), Decimal(1), Decimal(1), Decimal(1)],
    )

    for heading in headings:
        table.add(heading_helper(heading))

    for row_num, item in enumerate(line_items):

        table.add(row_content_helper(item.description))
        table.add(row_content_helper(str(item.quantity)))
        table.add(row_content_helper(format_money(item.price_per_unit)))
        table.add(row_content_helper(format_money(item.price())))

    table.even_odd_row_colors(
        even_row_color=COLOR['light_grey_blue'],
        odd_row_color=COLOR['lighter_grey_blue'],
        header_row_color=COLOR['dark_blue'],
    )

    table.set_padding_on_all_cells(
        padding_top=Decimal(7),
        padding_right=Decimal(5),
        padding_bottom=Decimal(2),
        padding_left=Decimal(5),
    )

    table.no_borders()

    return table
