"""Unit tests for kscinvoicing.web.profile_store."""
import pytest
import kscinvoicing.web.profile_store as ps


@pytest.fixture(autouse=True)
def patch_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ps, "SENDER_FILE", tmp_path / "sender.json")
    monkeypatch.setattr(ps, "CLIENTS_FILE", tmp_path / "clients.json")
    monkeypatch.setattr(ps, "LINE_ITEM_HISTORY_FILE", tmp_path / "line_item_history.json")


# ---------------------------------------------------------------------------
# Sender
# ---------------------------------------------------------------------------

def test_load_sender_returns_none_when_missing():
    assert ps.load_sender() is None


def test_save_load_sender_roundtrip():
    data = {"name": "Alice", "company": "ACME", "siren": "123456789", "email": "alice@acme.com"}
    ps.save_sender(data)
    result = ps.load_sender()
    assert result == data


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

def test_load_clients_returns_empty_when_missing():
    assert ps.load_clients() == {}


def test_save_load_client_individual():
    entry = {"type": "individual", "name": "Bob", "email": "bob@example.com"}
    ps.save_client("Bob", entry)
    clients = ps.load_clients()
    assert "Bob" in clients
    assert clients["Bob"] == entry


def test_save_load_client_company():
    entry = {
        "type": "company",
        "name": "Carol",
        "company_name": "Carol Corp",
        "siren": "987654321",
        "email": "carol@corp.com",
    }
    ps.save_client("Carol Corp", entry)
    clients = ps.load_clients()
    assert clients["Carol Corp"]["siren"] == "987654321"
    assert clients["Carol Corp"]["type"] == "company"


def test_delete_client_removes_key():
    ps.save_client("To Delete", {"type": "individual", "name": "X", "email": "x@x.com"})
    ps.delete_client("To Delete")
    assert "To Delete" not in ps.load_clients()


def test_delete_client_noop_if_missing():
    # Should not raise even if key doesn't exist
    ps.delete_client("nonexistent")
    assert ps.load_clients() == {}


# ---------------------------------------------------------------------------
# Line item history
# ---------------------------------------------------------------------------

def test_load_line_item_history_returns_empty_when_missing():
    assert ps.load_line_item_history() == {}


def test_record_line_items_creates_history_on_first_call():
    ps.record_line_items([{"description": "Consulting", "quantity": 2, "price_per_unit": "150.00"}])
    history = ps.load_line_item_history()
    assert "Consulting" in history
    assert history["Consulting"]["count"] == 1
    assert history["Consulting"]["quantity"] == 2
    assert history["Consulting"]["price_per_unit"] == "150.00"


def test_record_line_items_increments_count_on_repeat():
    item = {"description": "Consulting", "quantity": 1, "price_per_unit": "100.00"}
    ps.record_line_items([item])
    ps.record_line_items([item])
    history = ps.load_line_item_history()
    assert history["Consulting"]["count"] == 2


def test_record_line_items_updates_qty_and_price():
    ps.record_line_items([{"description": "Dev", "quantity": 1, "price_per_unit": "100.00"}])
    ps.record_line_items([{"description": "Dev", "quantity": 5, "price_per_unit": "200.00"}])
    history = ps.load_line_item_history()
    assert history["Dev"]["quantity"] == 5
    assert history["Dev"]["price_per_unit"] == "200.00"


def test_load_line_item_history_sorted_by_count_desc():
    ps.record_line_items([{"description": "A", "quantity": 1, "price_per_unit": "10"}])
    ps.record_line_items([{"description": "B", "quantity": 1, "price_per_unit": "10"}])
    ps.record_line_items([{"description": "B", "quantity": 1, "price_per_unit": "10"}])
    ps.record_line_items([{"description": "B", "quantity": 1, "price_per_unit": "10"}])
    history = ps.load_line_item_history()
    keys = list(history.keys())
    assert keys[0] == "B"
    assert keys[1] == "A"
