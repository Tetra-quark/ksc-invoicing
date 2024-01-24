from dataclasses import dataclass
import re


@dataclass
class Address:
    number: str
    street: str
    postcode: str
    city: str
    country: str

    def __str__(self) -> str:
        return f"{self.number} {self.street}\n{self.postcode} {self.city}, {self.country}"

    def address_lines(self) -> list:
        """Depends on the str method."""
        return str(self).split('\n')

    @property
    def line1(self):
        return self.address_lines()[0]

    @property
    def line2(self):
        return self.address_lines()[1]


# Generally its a good idea to seperate class use from class creation using factories
class AddressFactory:

    @staticmethod
    def create_address_from_str(address: str) -> Address:

        # use python's named groups regex extension
        pattern = r'(?P<number>\d+)\s(?P<street>[\w\s]+);\s' \
                  r'(?P<postcode>\d+[\w]+)\s(?P<city>[\w\s-]+),\s(?P<country>[\w\s-]+)'

        res = re.search(pattern, address)
        parsed_address_data = res.groupdict()

        # unpack kwargs
        return Address(**parsed_address_data)
