import unittest
from generate_invoice_from_json import generate_invoice
from kscinvoicing.pdf.borbinvoice import BorbInvoice

class TestGenerateInvoiceFromJson(unittest.TestCase):

    def setUp(self):
        self.invoice_data = {
            'logo_path': './example_config/example_logo.png',
            'save_location': './',
            'invoice_date': '2023-09-04',
            'footer_text': 'Some legal text.',
            'sender': {
                'name': 'Alice Sender',
                'phone': '(+33) 0123456789',
                'email': 'alice@sender.com',
                'website': None,
                'company': 'QuBit Technologies', 'siren': '123456789',
                'address': {
                    'number': '',
                    'street': 'Gower St',
                    'postcode': 'WC1E 6BT',
                    'city': 'London',
                    'country': 'United Kingdom'
                }
            },
            'recipient': {
                'name': 'Bob Recipient',
                'phone': None,
                'email': 'bob@recipient.com',
                'address': {
                    'number': '386',
                    'street': 'Rte de Meyrin',
                    'postcode': '1217',
                    'city': 'Meyrin',
                    'country': 'Switzerland'
                }
            },
            'lineitem_details': [
                {
                    'description': 'service 42',
                    'quantity': 3,
                    'price_per_unit': 50.0,
                },
                {
                    'description': 'product 505',
                    'quantity': 1,
                    'price_per_unit': 234
                }
            ]
        }

    def test_generate_invoice(self):
        borb_invoice = generate_invoice(self.invoice_data)

        self.assertIsInstance(borb_invoice, BorbInvoice)
        self.assertIsNotNone(borb_invoice.invoice)
        self.assertIsNotNone(borb_invoice.document)
        self.assertEqual(borb_invoice.invoice.sender.name, 'Alice Sender')
        self.assertEqual(len(borb_invoice.invoice.items), 2)
