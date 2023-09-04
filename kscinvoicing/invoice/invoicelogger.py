from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class InvoiceLogger:

    log_path: str

    @property
    def invoice_number(self):
        # TODO seperate invoice logging from the invoice class... pass invoice number to the invoice class.
        """Get next invoice number by incrementing last invoice number from log file by one.
        Or if not found it is first invoice."""
        try:
            with open(self.log_path, 'r') as log:
                d = json.load(log)
                prev_no = max([int(key) for key in d.keys()])
                invoice_number = f"{prev_no + 1:04}"
        except FileNotFoundError:
            # TODO not a safe way to handle this.. file could be not found for many reasons..
            invoice_number = "0001"

        return invoice_number

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
