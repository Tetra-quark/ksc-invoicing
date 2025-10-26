import argparse
from kscinvoicing.generate_invoice_from_json import invoice_data_from_json, generate_invoice_and_preview, generate_invoice_and_save


def cli():

    parser = argparse.ArgumentParser(description="Generate invoice from json file.")
    parser.add_argument("filepath", type=str, help="path to json file")
    parser.add_argument("--no-preview", action='store_false', help="open generated draft invoice in default pdf viewer")
    args = parser.parse_args()

    show_preview = args.no_preview # slightly confusing name
    data = invoice_data_from_json(args.filepath)

    if show_preview:
        generate_invoice_and_preview(data)
    else:
        generate_invoice_and_save(data)


if __name__ == '__main__':
    cli()
