import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

from borb.pdf import Document, PDF

from kscinvoicing.invoice import InvoiceData


@dataclass
class BorbInvoice:
    invoice: InvoiceData
    document: Document

    def _save_document(self, save_path: Path) -> None:
        with open(save_path, "wb") as f:
            # noinspection PyTypeChecker
            PDF.dumps(f, self.document)

    def _delete_draft(self):
        save_path = self._get_save_path(draft=True)
        save_path.unlink()

    def _get_save_path(self, draft: bool = False) -> Path:
        if draft:
            return self.invoice.save_folder / f"DRAFT_{self.invoice.get_invoice_name()}.pdf"
        else:
            return self.invoice.save_folder / f"{self.invoice.get_invoice_name()}.pdf"

    def save(self):
        """Save and log invoice with no preview."""
        save_path = self._get_save_path()
        self._save_document(save_path)
        print(f"Invoice saved to: '{save_path}'")
        self.invoice.log_invoice()


    def preview_with_optional_save(self):
        """Preview invoice before optional save and log."""
        save_path = self._get_save_path(draft=True)
        self._save_document(save_path)
        preview_file(save_path)
        response = input("Do you want to save this draft as an official invoice? (type 'y' to save)\n")
        if response == "y":
            # rename draft to final name
            save_path.rename(self._get_save_path())
            print(f"InvoiceData saved to : '{save_path}'")
            self.invoice.log_invoice()
        else:
            save_path.unlink()
            print("Draft deleted.")


def preview_file(file_path: Path):
    """
    Open the generated draft invoice in the default PDF viewer based on the OS.
    """
    system = platform.system()
    if system == "Windows":
        subprocess.run(['start', file_path], shell=True, check=True)
    elif system == "Darwin":  # macOS
        subprocess.run(['open', file_path], check=True)
    elif system == "Linux":
        subprocess.run(['xdg-open', file_path], check=True)
    else:
        print(f"Preview unavailable for OS: {system}. Please open the file manually: {file_path}")
