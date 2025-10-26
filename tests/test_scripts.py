import unittest
from unittest.mock import patch

from scripts import example, example_from_json


class TestScripts(unittest.TestCase):

    @patch('builtins.input', return_value='n')
    @patch('kscinvoicing.pdf.borbinvoice.preview_file') # prevent preview
    def test_example(self, mock_input, mock_preview):
        example.main()

    @patch('builtins.input', return_value='n')
    @patch('kscinvoicing.pdf.borbinvoice.preview_file')
    def test_example_from_json(self, mock_input, mock_preview):
        example_from_json.main()
