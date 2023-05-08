from dataclasses import dataclass
from typing import Optional

from kscadmin.address import Address


# client can be a company or an individual but min requirements are: name, adress, email
@dataclass
class ContactInfo:
    name: str
    address: Address
    email: str
    phone: Optional[str] = None
    website: Optional[str] = None
