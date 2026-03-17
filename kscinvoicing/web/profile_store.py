"""
Profile persistence layer for the Streamlit web UI.
Reads/writes project-local JSON files in ./kscinvoicing_data/.
No Streamlit dependency — independently testable.
"""
import json
from pathlib import Path

DATA_DIR = Path("kscinvoicing_data")
SENDER_FILE = DATA_DIR / "sender.json"
CLIENTS_FILE = DATA_DIR / "clients.json"
LINE_ITEM_HISTORY_FILE = DATA_DIR / "line_item_history.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Sender
# ---------------------------------------------------------------------------

def load_sender() -> dict | None:
    if not SENDER_FILE.exists():
        return None
    with open(SENDER_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_sender(data: dict) -> None:
    _ensure_data_dir()
    with open(SENDER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

def load_clients() -> dict:
    """Return dict keyed by client display name."""
    if not CLIENTS_FILE.exists():
        return {}
    with open(CLIENTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_client(key: str, data: dict) -> None:
    _ensure_data_dir()
    clients = load_clients()
    clients[key] = data
    with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(clients, f, indent=2, ensure_ascii=False)


def delete_client(key: str) -> None:
    clients = load_clients()
    clients.pop(key, None)
    with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(clients, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Line item history
# ---------------------------------------------------------------------------

def load_line_item_history() -> dict:
    """Return dict keyed by description string, sorted by usage count descending."""
    if not LINE_ITEM_HISTORY_FILE.exists():
        return {}
    with open(LINE_ITEM_HISTORY_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return dict(sorted(data.items(), key=lambda x: x[1]["count"], reverse=True))


def record_line_items(items: list[dict]) -> None:
    """Update history with the descriptions/quantities/prices from a generated invoice."""
    _ensure_data_dir()
    history = load_line_item_history()
    for item in items:
        desc = item["description"]
        if desc in history:
            history[desc]["count"] += 1
            history[desc]["quantity"] = item["quantity"]
            history[desc]["price_per_unit"] = str(item["price_per_unit"])
        else:
            history[desc] = {
                "quantity": item["quantity"],
                "price_per_unit": str(item["price_per_unit"]),
                "count": 1,
            }
    with open(LINE_ITEM_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
