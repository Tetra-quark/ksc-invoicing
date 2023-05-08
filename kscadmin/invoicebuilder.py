from borb.pdf.document import Document
from borb.pdf.page.page import Page
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.image.image import Image
from borb.pdf.canvas.layout.layout_element import Alignment
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.layout.table.table import TableCell
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.color.color import RGBColor
from borb.pdf.canvas.font.simple_font.true_type_font import TrueTypeFont
from borb.pdf.canvas.font.font import Font
from borb.pdf.canvas.geometry.rectangle import Rectangle
from borb.pdf.pdf import PDF

from pathlib import Path
from datetime import datetime
from typing import Optional
from decimal import Decimal
from dataclasses import dataclass

from kscadmin.contactinfo import ContactInfo
from kscadmin.invoice import LineItem, Invoice

# for french currency
import locale

locale.setlocale(locale.LC_ALL, 'fr_FR')

CURRENCY_SYMBOL = "€"

COLOR = {
    'white': RGBColor(Decimal(1), Decimal(1), Decimal(1)),
    'dark_blue': RGBColor(Decimal(0.14), Decimal(0.25), Decimal(0.445)),
    'grey_blue': RGBColor(Decimal(0.9), Decimal(0.9), Decimal(0.95))
}

# TODO need to make this accessible from within the library... for other users.
FONTBOOK = {
    "sf-compact-rounded": "/System/Library/Fonts/SFCompactRounded.ttf",
    "din-alternate-bold": "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf",
    "arial-rounded-bold": "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
    "veranda": "/System/Library/Fonts/Supplemental/Verdana.ttf",
    "trebuchet-ms": "/System/Library/Fonts/Supplemental/Trebuchet MS.ttf"
}


def get_font(font='veranda'):
    font_path = Path(FONTBOOK[font])
    font: Font = TrueTypeFont.true_type_font_from_file(font_path)

    return font


FONT = get_font('sf-compact-rounded')
FONT_BOLD = get_font('din-alternate-bold')


class VerticalSpacer(FixedColumnWidthTable):
    """Helper class to add vertical space of precise size to document."""

    def __init__(self, size: Decimal = Decimal('0')):
        super().__init__(number_of_rows=1, number_of_columns=1)
        self.add(Paragraph(" "))
        self.set_padding_on_all_cells(size, Decimal(1), Decimal(1), Decimal(1))
        self.no_borders()


@dataclass
class TableSchema:
    """Class to build borb table for invoice."""

    tabledata: list[list[str]]
    column_widths: list[Decimal]  # effectively these are ratios for a fixed width borb table
    bold_cells: list[tuple[int, int]]

    def __post_init__(self):

        self.n_rows = len(self.tabledata)
        self.n_cols = len(self.tabledata[0])

        # validate string_rep
        for row in self.tabledata[1:]:
            if self.n_cols != len(row):
                raise ValueError("The number of columns in the input table is inconsistent across rows.")

        # validate column_widths
        if self.n_cols != len(self.column_widths):
            raise ValueError("Column widths specified do not match the input table.")

    def build_table(self) -> FixedColumnWidthTable:
        """Build borb table from a TableSchema Object."""

        table = FixedColumnWidthTable(number_of_rows=self.n_rows,
                                      number_of_columns=self.n_cols,
                                      column_widths=self.column_widths)

        self.populate_table(table)

        # format table
        table.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(2), Decimal(2))
        table.no_borders()
        return table

    def populate_table(self, table):

        for i, row in enumerate(self.tabledata):
            for j, val in enumerate(row):
                font = FONT_BOLD if (i, j) in self.bold_cells else FONT
                table.add(Paragraph(val, font=font))


class InvoiceBuilder:

    def build_invoice(self,
                      siren_number: str,
                      sender: ContactInfo,
                      recipient: ContactInfo,
                      invoice: Invoice,
                      logopath: str,
                      footer_text: str = None) -> Document:
        """Main method to build invoice."""
        # TODO this could really do with better refactoring.. Do I split invoice build into more methods?
        #  Do have a master method that gets called once in main script or do I build the object method by method
        #  in the main script?
        #  What are the pros/cons of doing one over the other?

        logo = Image(Path(logopath), width=Decimal(182), height=Decimal(50))

        contact_details_schema = build_contact_details_schema(sender, recipient)
        contact_details_table = contact_details_schema.build_table()

        invoice_information_schema = build_invoice_info_schema(siren_number,
                                                               invoice.invoice_number,
                                                               invoice.date,
                                                               invoice.due_date)

        invoice_information_table = invoice_information_schema.build_table()

        itemised_table = build_itemised_table(invoice.items)

        totals_schema = build_totals_schema(invoice.subtotal,
                                            invoice.total,
                                            invoice.discount,
                                            invoice.tax)

        totals_table = totals_schema.build_table()

        pdf = self.build_invoice_document(logo,
                                          contact_details_table,
                                          invoice_information_table,
                                          itemised_table,
                                          totals_table,
                                          footer_text)

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


def build_invoice_info_schema(siren_number: str, invoice_number: str, bill_date: datetime,
                              due_date: Optional[datetime] = None) -> TableSchema:
    """ Inserts a table with the bill number, todays date and optionally the due date."""

    if due_date:
        due_date_label = "Due Date"
        due_date_value = due_date.strftime('%d/%m/%Y')
    else:
        due_date_label = " "
        due_date_value = " "

    # bill information
    tabledata = [["SIREN ", siren_number, "Facture Nº", invoice_number],
                 [" ", " ", "Date", bill_date.strftime('%d/%m/%Y')],
                 [" ", " ", due_date_label, due_date_value]]

    column_width_ratios = [Decimal(1), Decimal(5), Decimal(2), Decimal(2)]

    # specify cells to embolden
    bold_cells = [(0, 0), *[(i, 2) for i in range(len(tabledata))]]

    tableschema = TableSchema(tabledata, column_width_ratios, bold_cells)

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


def format_money(amount: Decimal, symbol: str = CURRENCY_SYMBOL) -> str:
    """Formats Decimal type for printing on invoice."""
    fmtd_amount = locale.currency(amount, grouping=True, symbol=False)
    return f"{symbol} {fmtd_amount}"
