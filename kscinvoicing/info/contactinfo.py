from dataclasses import dataclass
from typing import Optional

from kscinvoicing.info.address import Address


# client can be a company or an individual, but min requirements are: name, address, email
@dataclass
class ContactInfo:
    name: str
    address: Address
    email: str
    phone: Optional[str] = None
    website: Optional[str] = None
