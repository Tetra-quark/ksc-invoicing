from borb.pdf.document import Document
from borb.pdf.page.page import Page
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.image.image import Image
from borb.pdf.canvas.layout.layout_element import Alignment
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.layout.table.table import TableCell
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.geometry.rectangle import Rectangle
from borb.pdf.pdf import PDF

from pathlib import Path
from datetime import datetime
from typing import Optional
from decimal import Decimal

from kscinvoicing.info.contactinfo import ContactInfo
from kscinvoicing.invoice import LineItem, Invoice
from kscinvoicing.pdf.tableschema import TableSchema
from kscinvoicing.pdf.utils import VerticalSpacer, format_money
from kscinvoicing.pdf.utils import FONT, FONT_BOLD, COLOR


class InvoiceBuilder:

    def build_invoice(self,
                      siren_number: str,
                      company_name: str,
                      sender: ContactInfo,
                      recipient: ContactInfo,
                      invoice: Invoice,
                      logopath: str,
                      logo_width: int = 200,
                      footer_text: str = None) -> Document:
        """Main method to build invoice."""
        # TODO this could really do with better refactoring.. Do I split invoice build into more methods?
        #  Do have a master method that gets called once in main script or do I build the object method by method
        #  in the main script?
        #  What are the pros/cons of doing one over the other?

        def get_image_dimensions(path) -> tuple[int, int]:
            from PIL import Image as PILImage
            logo_pil = PILImage.open(path)
            return logo_pil.size

        w, h = get_image_dimensions(logopath)
        logo_height = logo_width * h // w

        logo = Image(Path(logopath), width=Decimal(logo_width), height=Decimal(logo_height))

        contact_details_schema = build_contact_details_schema(sender, recipient)
        contact_details_table = contact_details_schema.build_table()

        invoice_information_schema = build_invoice_info_schema(company_name=company_name,
                                                               siren_number=siren_number,
                                                               invoice_number=invoice.invoice_number,
                                                               bill_date=invoice.date,
                                                               due_date=invoice.due_date)
        invoice_information_table = invoice_information_schema.build_table()

        itemised_table = build_itemised_table(invoice.items)

        totals_schema = build_totals_schema(subtotal=invoice.subtotal,
                                            total=invoice.total,
                                            discount=invoice.discount,
                                            tax=invoice.tax)
        totals_table = totals_schema.build_table()

        pdf = self.build_invoice_document(logo=logo,
                                          contact_details_table=contact_details_table,
                                          invoice_information_table=invoice_information_table,
                                          itemised_table=itemised_table,
                                          totals_table=totals_table,
                                          footer_text=footer_text)

        return pdf

    @staticmethod
    def build_invoice_document(logo: Image,
                               contact_details_table: FixedColumnWidthTable,
                               invoice_information_table: FixedColumnWidthTable,
                               itemised_table: FixedColumnWidthTable,
                               totals_table: FixedColumnWidthTable,
                               footer_text: str) -> Document:
        """Creates a pdf object for invoice using borb tables."""
        # Create document & add page
        pdf = Document()
        page = Page()
        pdf.append_page(page)

        # layout
        layout = SingleColumnLayout(page)
        layout.vertical_margin = page.get_page_info().get_height() * Decimal(0.02)

        layout.add(logo)
        layout.add(Paragraph(" "))  # vertical space
        layout.add(contact_details_table)  # Invoice personal & recipient information
        layout.add(VerticalSpacer(size=Decimal('15')))
        layout.add(invoice_information_table)  # Invoice information (date etc, invoice number)
        layout.add(VerticalSpacer(size=Decimal('5')))
        layout.add(itemised_table)  # Invoice items
        layout.add(VerticalSpacer(size=Decimal('10')))
        layout.add(totals_table)  # Invoice totals summary
        if footer_text:
            add_footer(page, footer_text)

        return pdf

    @staticmethod
    def save_document(savepath: Path, document: Document) -> None:
        with open(savepath, "wb") as f:
            # noinspection PyTypeChecker
            PDF.dumps(f, document)


def add_footer(page: Page, footer_text: str):
    """Places a centered footer at the bottom of the page."""
    ps = page.get_page_info().get_size()
    rect = Rectangle(Decimal(0), Decimal(0), Decimal(ps[0]), Decimal(60))
    footer = Paragraph(footer_text, font_size=Decimal(8), font=FONT, horizontal_alignment=Alignment.CENTERED)
    footer.layout(page, rect)


def build_invoice_info_schema(company_name: str, siren_number: str, invoice_number: str, bill_date: datetime,
                              due_date: Optional[datetime] = None) -> TableSchema:
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


def build_contact_details_schema(sender: ContactInfo, recipient: ContactInfo) -> TableSchema:
    """ Inserts a table with sender and recipient personal information."""

    # TODO ideally the information necessary should be passed into here and this method should not rely on
    #  implementation details of the ContactInfo class.. Two options: pass info as arguments, or split method and
    #  implement some of it in the ContactInfo class? or Invoice class? Inferfaces?

    # sender and recipient personal information table layout
    tabledata = [[f"Facturé par", " ", "Facturé à"],
                 [sender.name, " ", recipient.name],
                 [sender.address.line1, " ", recipient.address.line1],
                 [sender.address.line2, " ", recipient.address.line2],
                 [sender.phone, " ", recipient.email],
                 [sender.email, " ", " "]]

    # Bold headings
    bold_cells = [(0, 0), (0, 2)]
    column_width_ratios = [Decimal(2), Decimal(1), Decimal(2)]

    tableschema = TableSchema(tabledata=tabledata,
                              column_widths=column_width_ratios,
                              bold_cells=bold_cells)

    return tableschema


def build_totals_schema(subtotal: Decimal,
                        total: Decimal,
                        discount: Decimal,
                        tax: Decimal) -> TableSchema:
    """Builds TableSchema """

    tabledata = []

    def row_helper(label: str, value: str) -> list[str]:
        return [" ", label, value]

    # don't show totals if unneccesary, is there a better way to write this logic?
    if discount != Decimal('0') or tax != Decimal('0'):
        fmt_subtotal = format_money(subtotal)
        tabledata.append(row_helper("Sous-Total", fmt_subtotal))

        if discount != Decimal('0'):
            fmt_discount = format_money(discount)
            tabledata.append(row_helper("Remise Total", fmt_discount))

        if tax != Decimal('0'):
            fmt_tax = format_money(tax)
            tabledata.append(row_helper("TVA", fmt_tax))

    # grand total
    fmt_total = format_money(total)
    tabledata.append(row_helper("Total", fmt_total))

    bold_cells = [(i, 1) for i in range(len(tabledata))]
    column_width_ratios = [Decimal(4), Decimal(1), Decimal(1)]
    tableschema = TableSchema(tabledata=tabledata,
                              column_widths=column_width_ratios,
                              bold_cells=bold_cells)
    return tableschema


def build_itemised_table(line_items: list[LineItem]) -> FixedColumnWidthTable:
    """Builds Borb table containing line items for the invoice."""

    headings = ["Description", "Quantité", "Prix Unité", "Total"]

    table = FixedColumnWidthTable(number_of_rows=len(line_items) + 1,
                                  number_of_columns=4,
                                  column_widths=[Decimal(3), Decimal(1), Decimal(1), Decimal(1)])

    for heading in headings:
        p = Paragraph(heading,
                      font_color=COLOR['white'],
                      font=FONT_BOLD,
                      horizontal_alignment=Alignment.LEFT)
        table.add(TableCell(p, background_color=COLOR['dark_blue']))

    for row_num, item in enumerate(line_items):

        # color rows
        if row_num % 2 == 0:
            c = COLOR['grey_blue']
        else:
            c = COLOR['white']

        # row content
        table.add(TableCell(Paragraph(item.description, font=FONT), background_color=c))
        table.add(TableCell(Paragraph(str(item.quantity), font=FONT), background_color=c))
        table.add(TableCell(Paragraph(format_money(item.price_per_unit), font=FONT), background_color=c))
        table.add(TableCell(Paragraph(format_money(item.price()), font=FONT), background_color=c))

        table.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(10), Decimal(2))
        table.no_borders()

    return table
