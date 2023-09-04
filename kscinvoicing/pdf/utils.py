
# for french currency
import locale
from decimal import Decimal
from pathlib import Path

from borb.pdf.canvas.color.color import RGBColor
from borb.pdf.canvas.font.simple_font.true_type_font import TrueTypeFont
from borb.pdf.canvas.font.font import Font
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.layout.text.paragraph import Paragraph

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


def format_money(amount: Decimal, symbol: str = CURRENCY_SYMBOL) -> str:
    """Formats Decimal type for printing on invoice."""
    fmtd_amount = locale.currency(amount, grouping=True, symbol=False)
    return f"{symbol} {fmtd_amount}"


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
