from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json


@dataclass
class InvoiceLogger:

    log_path: Path
    _invoice_number: str = field(init=False, repr=True)

    def _get_previous_invoice_number(self) -> int:
        """Gets the largest invoice number in the log file."""
        with open(self.log_path, 'r') as log:
            d = json.load(log)
            prev_num = max([int(key) for key in d.keys()])
            return prev_num

    def __post_init__(self):
        try:
            # get previous invoice number and increment by 1
            prev_num = self._get_previous_invoice_number()
            self.invoice_number = f"{prev_num + 1:04}"
        except FileNotFoundError:
            print(f"WARNING: {self.log_path} was not found. If you proceed to save the invoice draft it will be "
                  f"created.")
            self.invoice_number = "0001"

    @property
    def invoice_number(self):
        return self._invoice_number

    @invoice_number.setter
    def invoice_number(self, number: str):
        self._invoice_number = number

    def log_invoice(self, date: datetime, sender: str, recipient: str, total: str):

        new_log = {
            "date": date.strftime("%d/%m/%Y"),
            "invoice_from": sender,
            "invoice_to": recipient,
            "total amount": str(total)
        }

        try:
            with open(self.log_path, 'r') as log:
                logdata = json.load(log)
        except FileNotFoundError:
            logdata = {}

        logdata[self.invoice_number] = new_log

        with open(self.log_path, 'w') as log:
            json.dump(logdata, log,
                      indent=4,
                      separators=(',', ': '))

        print("Logfile written to json")

