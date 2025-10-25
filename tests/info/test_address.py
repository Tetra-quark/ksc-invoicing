import unittest
from kscinvoicing.info.address import Address


class TestAddress(unittest.TestCase):

    def setUp(self):
        self.full_address = Address(
            number="1",
            street="Street",
            postcode="12345",
            city="City",
            country="Country",
            building="Building"
        )
        self.address_without_building = Address(
            number="1",
            street="Street",
            postcode="12345",
            city="City",
            country="Country",
        )

    def test_address_creation(self):

        self.assertEqual("1", self.full_address.number)
        self.assertEqual("Street", self.full_address.street)
        self.assertEqual("12345", self.full_address.postcode)
        self.assertEqual("City", self.full_address.city)
        self.assertEqual("Country", self.full_address.country)
        self.assertEqual("Building", self.full_address.building)

    def test_address_without_building(self):
        self.assertEqual(None, self.address_without_building.building)

    def test_full_address(self):
        self.assertEqual("Building\n1 Street\n12345 City, Country", self.full_address.full_address)
        self.assertEqual("1 Street\n12345 City, Country", self.address_without_building.full_address)

    def test_address_lines(self):
        self.assertEqual(["Building", "1 Street", "12345 City, Country"], self.full_address.address_lines())
        self.assertEqual(["1 Street", "12345 City, Country"], self.address_without_building.address_lines())
