# KSC Invoicing: A PDF Invoice Generator

## Description
A tool for generating PDF invoices.
Keeps track of invoice numbers and generating a new invoice number based a plaintext log file.
Generates PDF invoices from a json configuration file. 

## Why?
When I setup my freelance business - Koppanyi Scientific Consulting - under the French micro-enterprise status, 
I needed to create invoices that were legally compliant. I thought it would be a fun software project to make a tool to 
generate (and eventually manage) my invoices, while also giving them custom design. 

## Installation

```shell
conda env create -f env.yaml
conda activate kscinvoicing

```

## How to Use

```shell
python generate_invoice_from_json.py example_config/invoice.json

```

### Fonts
Fonts can be customised in the config file by supplying the path to a .ttf file. 
If no font is supplied, the default font will be used which is packaged with this repository.
The fonts used here were obtained from [Google Fonts](https://fonts.google.com/?preview.layout=grid&lang=en_Latn).


## TODO
- [ ] Update project to more recent version of Borb!

## Installation


## Disclaimer
This software is provided "as-is" without any warranty.
