"""
Example script to generate an invoice from a JSON file.
"""
from pathlib import Path
from kscinvoicing.generate_invoice_from_json import invoice_data_from_json, generate_invoice_and_preview

def main():

    # NOTE: The example logo will fail to display on this invoice unless the `logo_path` in
    # `example_config/invoice.json` is set relative the scripts directory i.e. "../example_config/example_logo.png".
    # By default it is set to work from the root directory for the CLI.
    file_path = Path(__file__).parents[1] / "example_config/invoice.json"
    data = invoice_data_from_json(str(file_path))
    generate_invoice_and_preview(data)


if __name__ == '__main__':
    main()
