import argparse
import sys
from pathlib import Path

from kscinvoicing.generate_invoice_from_json import invoice_data_from_json, generate_invoice_and_preview, generate_invoice_and_save

APP_PATH = Path(__file__).parent / "web" / "app.py"


def cli():
    parser = argparse.ArgumentParser(description="KSC invoicing tool.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate subcommand (existing behaviour)
    gen = subparsers.add_parser("generate", help="Generate invoice from a JSON file.")
    gen.add_argument("filepath", type=str, help="path to json file")
    gen.add_argument("--no-preview", action="store_false", dest="show_preview",
                     help="save invoice directly without opening a preview")

    # serve subcommand (new)
    serve = subparsers.add_parser("serve", help="Launch the Streamlit web UI.")
    serve.add_argument("--port", type=int, default=8501, help="port to serve on (default: 8501)")
    serve.add_argument("--host", type=str, default="localhost", help="host address (default: localhost)")

    args = parser.parse_args()

    if args.command == "generate":
        data = invoice_data_from_json(args.filepath)
        if args.show_preview:
            generate_invoice_and_preview(data)
        else:
            generate_invoice_and_save(data)

    elif args.command == "serve":
        import subprocess
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(APP_PATH),
            "--server.port", str(args.port),
            "--server.address", args.host,
        ])


if __name__ == '__main__':
    cli()
