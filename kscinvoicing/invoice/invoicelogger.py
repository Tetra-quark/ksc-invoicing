from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class InvoiceLogger:

    log_path: str
    _invoice_number: str = field(init=False, repr=True)

    def __post_init__(self):
        try:
            with open(self.log_path, 'r') as log:
                d = json.load(log)
                prev_no = max([int(key) for key in d.keys()])
                self.invoice_number = f"{prev_no + 1:04}"
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

    @staticmethod
    def generate_invoice_name(invoice_id: str, recipient_name: str, date: datetime):
        return f"Invoice_{invoice_id}_{recipient_name.replace(' ', '-')}_{date.strftime('%Y-%m-%d')}"
