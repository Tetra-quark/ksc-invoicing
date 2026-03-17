"""Unit tests for pure helper functions in kscinvoicing.web.app (no Streamlit runtime needed)."""
from kscinvoicing.web.app import _build_address, _build_sender, _build_recipient
from kscinvoicing.info import Address, CompanySender, IndividualRecipient, CompanyRecipient


# ---------------------------------------------------------------------------
# _build_address
# ---------------------------------------------------------------------------

def test_build_address_all_fields():
    d = {"number": "10", "street": "Rue de la Paix", "postcode": "75001",
         "city": "Paris", "country": "France", "building": "Bât A"}
    addr = _build_address(d)
    assert isinstance(addr, Address)
    assert addr.number == "10"
    assert addr.street == "Rue de la Paix"
    assert addr.postcode == "75001"
    assert addr.city == "Paris"
    assert addr.country == "France"
    assert addr.building == "Bât A"


def test_build_address_building_none_when_empty_string():
    d = {"number": "1", "street": "Main St", "postcode": "00000",
         "city": "Nowhere", "country": "FR", "building": ""}
    addr = _build_address(d)
    assert addr.building is None


def test_build_address_building_none_when_absent():
    d = {"number": "1", "street": "Main St", "postcode": "00000", "city": "Nowhere", "country": "FR"}
    addr = _build_address(d)
    assert addr.building is None


# ---------------------------------------------------------------------------
# _build_sender
# ---------------------------------------------------------------------------

def test_build_sender_constructs_company_sender():
    d = {
        "siren": "123456789",
        "company": "ACME SAS",
        "name": "Alice",
        "email": "alice@acme.com",
        "phone": "+33 6 00 00 00 00",
        "website": "https://acme.com",
        "address": {"number": "1", "street": "Rue A", "postcode": "75000",
                    "city": "Paris", "country": "France"},
    }
    sender = _build_sender(d)
    assert isinstance(sender, CompanySender)
    assert sender.siren == "123456789"
    assert sender.company_name == "ACME SAS"
    assert sender.name == "Alice"
    assert sender.email == "alice@acme.com"
    assert sender.phone == "+33 6 00 00 00 00"
    assert sender.website == "https://acme.com"


def test_build_sender_phone_and_website_none_when_empty():
    d = {
        "siren": "000000000", "company": "X", "name": "X",
        "email": "x@x.com", "phone": "", "website": "",
        "address": {},
    }
    sender = _build_sender(d)
    assert sender.phone is None
    assert sender.website is None


# ---------------------------------------------------------------------------
# _build_recipient
# ---------------------------------------------------------------------------

def test_build_recipient_individual():
    d = {"type": "individual", "name": "Bob", "email": "bob@example.com",
         "phone": None, "website": None, "address": {}}
    recipient = _build_recipient(d)
    assert isinstance(recipient, IndividualRecipient)
    assert recipient.name == "Bob"
    assert recipient.email == "bob@example.com"


def test_build_recipient_company():
    d = {
        "type": "company",
        "siren": "987654321",
        "company_name": "Bob Corp",
        "name": "Bob",
        "email": "bob@bobcorp.com",
        "phone": None,
        "website": None,
        "address": {},
    }
    recipient = _build_recipient(d)
    assert isinstance(recipient, CompanyRecipient)
    assert recipient.siren == "987654321"
    assert recipient.company_name == "Bob Corp"
    assert recipient.name == "Bob"


def test_build_recipient_missing_type_defaults_to_individual():
    d = {"name": "Carol", "email": "carol@example.com", "address": {}}
    recipient = _build_recipient(d)
    assert isinstance(recipient, IndividualRecipient)
