"""
Class for the different parties in an invoice.
"""
from dataclasses import dataclass
from kscinvoicing.info.address import Address

@dataclass
class CompanySender:
    siren: str
    company_name: str
    name: str
    address: Address
    email: str
    phone: str | None = None
    website: str | None = None


@dataclass
class IndividualRecipient:
    name: str
    address: Address
    email: str
    phone: str | None = None
    website: str | None = None


@dataclass
class CompanyRecipient:
    siren: str
    company_name: str
    name: str
    address: Address
    email: str
    phone: str | None = None
    website: str | None = None
