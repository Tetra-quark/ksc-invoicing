import locale # for french currency
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
import json

from borb.pdf import (
    RGBColor,
    TrueTypeFont,
    FixedColumnWidthTable,
    Paragraph,
)

locale.setlocale(locale.LC_ALL, 'fr_FR')
locale._override_localeconv['n_sign_posn'] = 1

CURRENCY_SYMBOL = "€"

COLOR = {
    'white': RGBColor(Decimal(1), Decimal(1), Decimal(1)),
    'light_grey_blue': RGBColor(Decimal(0.85), Decimal(0.85), Decimal(0.93)),
    'lighter_grey_blue': RGBColor(Decimal(0.94), Decimal(0.94), Decimal(0.99)),
    'dark_blue': RGBColor(Decimal(0.14), Decimal(0.25), Decimal(0.445)),
}


def clean_text(val):
    """Helper function to clean text. To avoid error related to uncommon whitespace for Roboto font."""
    return val.replace('\u202F', ' ')


def format_money(amount: Decimal, symbol: str = CURRENCY_SYMBOL) -> str:
    """Formats Decimal type for printing on invoice."""
    fmtd_amount = locale.currency(amount, grouping=True, symbol=False)
    output = symbol + " " + clean_text(fmtd_amount)
    return output


CONFIG_FOLDER = Path(__file__).parents[2] / "config"

@dataclass
class StyleConfig:
    cfg: dict
    primary_font: TrueTypeFont = field(init=False)
    title_font: TrueTypeFont = field(init=False)

    @staticmethod
    def load_font(font_path: str) -> TrueTypeFont:
        return TrueTypeFont.true_type_font_from_file(CONFIG_FOLDER / font_path)

    def __post_init__(self):
        self.primary_font = self.load_font(self.cfg['primary_font'])
        self.title_font = self.load_font(self.cfg['title_font'])


def load_style_config() -> StyleConfig:
    """Load style configuration from json file."""
    style_path = CONFIG_FOLDER / "style.json"
    with open(style_path, "r") as file:
        style_cfg = json.load(file)
    style = StyleConfig(style_cfg)
    return style

STYLE = load_style_config()

class VerticalSpacer(FixedColumnWidthTable):
    """Helper class to add vertical space of precise size to document."""

    def __init__(self, size: Decimal = Decimal('0')):
        super().__init__(number_of_rows=1, number_of_columns=1)
        self.add(Paragraph(" "))
        self.set_padding_on_all_cells(size, Decimal(1), Decimal(1), Decimal(1))
        self.no_borders()
