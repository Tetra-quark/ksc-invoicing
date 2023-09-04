from decimal import Decimal
from dataclasses import dataclass, field
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.table.table import TableCell

from kscinvoicing.pdf.utils import FONT, FONT_BOLD


@dataclass
class TableSchema:
    """Class to build borb table for invoice."""

    tabledata: list[list[str]]
    column_widths: list[Decimal]  # effectively these are ratios for a fixed width borb table
    bold_cells: list[tuple[int, int]]
    double_cells: list[tuple[int, int]] = field(default_factory=lambda: [])  # merges righthand cell with specified cell

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

        ignore_cells = []
        for i, row in enumerate(self.tabledata):
            for j, val in enumerate(row):

                if (i, j) in ignore_cells:
                    continue

                font = FONT_BOLD if (i, j) in self.bold_cells else FONT
                text = Paragraph(val, font=font)

                if (i, j) in self.double_cells:
                    table.add(TableCell(text, col_span=2))
                    ignore_cells.append((i, j+1))
                else:
                    table.add(text)
