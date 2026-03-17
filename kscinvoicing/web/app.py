"""
Streamlit web UI for ksc-invoicing.
Launch via: kscinvoicing serve
"""
import tempfile
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

import streamlit as st

from kscinvoicing.web import profile_store
from kscinvoicing.info import Address, CompanySender, IndividualRecipient, CompanyRecipient
from kscinvoicing.invoice import LineItem, InvoiceData
from kscinvoicing.pdf.invoicebuilder import build_invoice

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def _init_state():
    st.session_state.setdefault("line_items", [{"description": "", "desc_mode": "history", "quantity": 1, "price_per_unit": 0.0}])
    st.session_state.setdefault("generated_pdf_path", None)
    st.session_state.setdefault("delete_confirm", False)


# ---------------------------------------------------------------------------
# Helper – build domain objects from form dicts
# ---------------------------------------------------------------------------

def _build_address(d: dict) -> Address:
    return Address(
        number=d.get("number", ""),
        street=d.get("street", ""),
        postcode=d.get("postcode", ""),
        city=d.get("city", ""),
        country=d.get("country", ""),
        building=d.get("building") or None,
    )


def _build_sender(d: dict) -> CompanySender:
    return CompanySender(
        siren=d.get("siren", ""),
        company_name=d.get("company", ""),
        name=d.get("name", ""),
        address=_build_address(d.get("address", {})),
        email=d.get("email", ""),
        phone=d.get("phone") or None,
        website=d.get("website") or None,
    )


def _build_recipient(d: dict) -> IndividualRecipient | CompanyRecipient:
    addr = _build_address(d.get("address", {}))
    if d.get("type") == "company":
        return CompanyRecipient(
            siren=d.get("siren", ""),
            company_name=d.get("company_name", ""),
            name=d.get("name", ""),
            address=addr,
            email=d.get("email", ""),
            phone=d.get("phone") or None,
            website=d.get("website") or None,
        )
    return IndividualRecipient(
        name=d.get("name", ""),
        address=addr,
        email=d.get("email", ""),
        phone=d.get("phone") or None,
        website=d.get("website") or None,
    )


# ---------------------------------------------------------------------------
# Reusable address form widget (returns dict)
# ---------------------------------------------------------------------------

def _address_form(prefix: str, defaults: dict) -> dict:
    c1, c2 = st.columns([1, 4])
    number = c1.text_input("No.", value=defaults.get("number", ""), key=f"{prefix}_number")
    street = c2.text_input("Street", value=defaults.get("street", ""), key=f"{prefix}_street")
    building = st.text_input("Building (optional)", value=defaults.get("building", "") or "", key=f"{prefix}_building")
    c3, c4, c5 = st.columns(3)
    postcode = c3.text_input("Postcode", value=defaults.get("postcode", ""), key=f"{prefix}_postcode")
    city = c4.text_input("City", value=defaults.get("city", ""), key=f"{prefix}_city")
    country = c5.text_input("Country", value=defaults.get("country", ""), key=f"{prefix}_country")
    return {"number": number, "street": street, "building": building,
            "postcode": postcode, "city": city, "country": country}


# ---------------------------------------------------------------------------
# Tab 1: Generate Invoice
# ---------------------------------------------------------------------------

def _tab_generate():
    history = profile_store.load_line_item_history()
    history_keys = list(history.keys())

    # ---- Sender ----
    st.subheader("Sender")
    saved_sender = profile_store.load_sender()
    if saved_sender:
        st.info(f"**{saved_sender.get('name', '')}** — {saved_sender.get('company', '')} | {saved_sender.get('email', '')}")
    else:
        st.warning("No sender profile saved. Go to the Sender Profile tab.")

    # ---- Client ----
    st.subheader("Client")
    clients = profile_store.load_clients()
    if not clients:
        st.warning("No clients saved. Go to the Manage Clients tab.")
        selected_client = None
    else:
        client_options = list(clients.keys())
        selected_client = st.selectbox("Select client", client_options, key="selected_client_gen")
        c_data = clients[selected_client]
        type_label = "Company" if c_data.get("type") == "company" else "Individual"
        company_info = f" — {c_data['company_name']}" if c_data.get("type") == "company" else ""
        st.info(f"**{selected_client}**{company_info} ({type_label}) | {c_data.get('email', '')}")

    # ---- Line items ----
    st.subheader("Line items")

    items_to_delete = []
    for i, item in enumerate(st.session_state["line_items"]):
        c1, c2, c3, c4 = st.columns([4, 1, 1.5, 0.5])

        mode_options = ["-- Custom --"] + history_keys
        current_desc = item.get("description", "")
        default_mode_idx = history_keys.index(current_desc) + 1 if current_desc in history_keys else 0
        chosen = c1.selectbox("Description", mode_options, index=default_mode_idx, key=f"item_desc_sel_{i}",
                               label_visibility="collapsed")

        if chosen == "-- Custom --":
            desc = c1.text_input("Custom description", value=current_desc, key=f"item_desc_txt_{i}",
                                  label_visibility="collapsed", placeholder="Description")
            qty_default = item.get("quantity", 1)
            price_default = item.get("price_per_unit", 0.0)
        else:
            desc = chosen
            hist = history.get(chosen, {})
            qty_default = hist.get("quantity", item.get("quantity", 1))
            price_default = float(hist.get("price_per_unit", item.get("price_per_unit", 0.0)))

        qty = c2.number_input("Qty", min_value=1, value=int(qty_default), step=1,
                               key=f"item_qty_{i}", label_visibility="collapsed")
        price = c3.number_input("Price/unit", min_value=0.0, value=float(price_default),
                                 step=0.01, format="%.2f", key=f"item_price_{i}",
                                 label_visibility="collapsed")

        st.session_state["line_items"][i] = {"description": desc, "quantity": qty, "price_per_unit": price}

        if c4.button("✕", key=f"del_item_{i}"):
            items_to_delete.append(i)

    for idx in reversed(items_to_delete):
        st.session_state["line_items"].pop(idx)
        st.rerun()

    if st.button("+ Add line item"):
        st.session_state["line_items"].append({"description": "", "quantity": 1, "price_per_unit": 0.0})
        st.rerun()

    # ---- Invoice settings ----
    st.subheader("Invoice settings")
    c1, c2 = st.columns(2)
    invoice_date = c1.date_input("Invoice date", value=date.today(), key="inv_date")
    due_date_enabled = c2.checkbox("Set due date", key="due_date_enabled")
    due_date = c2.date_input("Due date", value=date.today(), key="inv_due_date",
                              disabled=not due_date_enabled)

    c1, c2, c3 = st.columns(3)
    currency = c1.selectbox("Currency", ["EUR", "USD", "GBP", "CHF"], key="inv_currency")
    language = c2.selectbox("Language", ["fr", "en"], key="inv_language")
    logo_width = c3.number_input("Logo width (px)", min_value=50, max_value=600,
                                   value=200, step=10, key="inv_logo_width")

    c1, c2 = st.columns(2)
    discount = c1.number_input("Discount (fixed amount)", min_value=0.0, value=0.0,
                                 step=0.01, format="%.2f", key="inv_discount")
    tax_rate = c2.number_input("Tax rate (0.20 = 20%)", min_value=0.0, max_value=1.0,
                                 value=0.0, step=0.01, format="%.2f", key="inv_tax_rate")

    logo_file = st.file_uploader("Logo (PNG/JPG, optional)", type=["png", "jpg", "jpeg"],
                                   key="inv_logo")
    footer_text = st.text_area("Footer text (optional)", key="inv_footer")
    save_folder = st.text_input("Save folder", value="invoices", key="inv_save_folder")

    # ---- Generate ----
    st.divider()
    if st.button("Generate Invoice", type="primary"):
        errors = []
        if saved_sender is None:
            errors.append("No sender profile saved. Go to the Sender Profile tab.")
        if selected_client is None:
            errors.append("No clients saved. Add a client in the Manage Clients tab.")
        valid_items = [it for it in st.session_state["line_items"] if it.get("description")]
        if not valid_items:
            errors.append("At least one line item with a description is required.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            try:
                sender_obj = _build_sender(saved_sender)
                recipient_obj = _build_recipient(clients[selected_client])
                line_item_objs = [
                    LineItem(
                        description=it["description"],
                        quantity=int(it["quantity"]),
                        price_per_unit=Decimal(str(it["price_per_unit"])),
                    )
                    for it in valid_items
                ]

                folder = Path(save_folder)
                folder.mkdir(parents=True, exist_ok=True)

                invoice_dt = datetime.combine(invoice_date, datetime.min.time())
                due_dt = datetime.combine(due_date, datetime.min.time()) if due_date_enabled else None

                invoice_data = InvoiceData(
                    sender=sender_obj,
                    recipient=recipient_obj,
                    items=line_item_objs,
                    save_folder=folder,
                    currency=currency,
                    date=invoice_dt,
                    due_date=due_dt,
                    discount=Decimal(str(discount)),
                    tax_rate=Decimal(str(tax_rate)),
                )

                logo_path = None
                tmp_dir = None
                if logo_file is not None:
                    tmp_dir = tempfile.mkdtemp()
                    logo_path = str(Path(tmp_dir) / logo_file.name)
                    with open(logo_path, "wb") as f:
                        f.write(logo_file.getvalue())

                borb_invoice = build_invoice(
                    invoice=invoice_data,
                    logo_path=logo_path,
                    logo_width=int(logo_width),
                    footer_text=footer_text or None,
                    language=language,
                )
                borb_invoice.save()

                profile_store.record_line_items([
                    {"description": it["description"], "quantity": int(it["quantity"]),
                     "price_per_unit": str(it["price_per_unit"])}
                    for it in valid_items
                ])

                if tmp_dir and logo_path:
                    Path(logo_path).unlink(missing_ok=True)

                pdf_path = folder / f"{invoice_data.get_invoice_name()}.pdf"
                st.success(f"Invoice saved to `{pdf_path}`")

                if pdf_path.exists():
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download PDF",
                            data=f.read(),
                            file_name=pdf_path.name,
                            mime="application/pdf",
                        )

            except Exception as e:
                st.error(f"Error generating invoice: {e}")


# ---------------------------------------------------------------------------
# Tab 2: Manage Clients
# ---------------------------------------------------------------------------

def _tab_clients():
    import pandas as pd

    clients = profile_store.load_clients()

    # ---- Client list ----
    st.subheader("Saved clients")
    selected_key = None
    if clients:
        rows = [
            {
                "Reference": key,
                "Type": "Company" if data.get("type") == "company" else "Individual",
                "Company": data.get("company_name", "") if data.get("type") == "company" else "",
                "Email": data.get("email", ""),
            }
            for key, data in clients.items()
        ]
        df = pd.DataFrame(rows)
        event = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )
        selected_rows = event.selection.rows if event else []
        if selected_rows:
            selected_key = rows[selected_rows[0]]["Reference"]
    else:
        st.info("No clients saved yet.")

    # ---- Edit selected client ----
    if selected_key:
        c_data = clients[selected_key]
        st.subheader(f"Edit: {selected_key}")
        is_co = c_data.get("type") == "company"

        e_ref_name = st.text_input("Reference name", value=selected_key, key=f"e_ref_name_{selected_key}")

        if is_co:
            c1, c2 = st.columns(2)
            e_company = c1.text_input("Company name", value=c_data.get("company_name", ""), key=f"e_company_{selected_key}")
            e_siren = c2.text_input("SIREN", value=c_data.get("siren", ""), key=f"e_siren_{selected_key}")
        else:
            e_company = ""
            e_siren = ""

        e_email = st.text_input("Email", value=c_data.get("email", ""), key=f"e_email_{selected_key}")
        c1, c2 = st.columns(2)
        e_phone = c1.text_input("Phone", value=c_data.get("phone", "") or "", key=f"e_phone_{selected_key}")
        e_website = c2.text_input("Website", value=c_data.get("website", "") or "", key=f"e_website_{selected_key}")
        st.markdown("**Address**")
        e_addr = _address_form(f"edit_client_{selected_key}", c_data.get("address", {}))

        c1, c2 = st.columns(2)
        if c1.button("Save changes", key="save_edit_c_btn"):
            entry = {
                "type": "company" if is_co else "individual",
                "name": e_ref_name, "email": e_email,
                "phone": e_phone or None, "website": e_website or None,
                "address": e_addr,
            }
            if is_co:
                entry["company_name"] = e_company
                entry["siren"] = e_siren
            if e_ref_name != selected_key:
                profile_store.delete_client(selected_key)
            profile_store.save_client(e_ref_name, entry)
            st.success("Client updated.")
            st.rerun()

        if c2.button("Delete client", key="delete_c_btn"):
            st.session_state["delete_confirm"] = True

        if st.session_state.get("delete_confirm"):
            st.warning(f"Delete **{selected_key}**? This cannot be undone.")
            col1, col2 = st.columns(2)
            if col1.button("Yes, delete", key="confirm_delete_btn"):
                profile_store.delete_client(selected_key)
                st.session_state["delete_confirm"] = False
                st.success(f"Client '{selected_key}' deleted.")
                st.rerun()
            if col2.button("Cancel", key="cancel_delete_btn"):
                st.session_state["delete_confirm"] = False
                st.rerun()

    # ---- Add new client ----
    with st.expander("+ Add new client"):
        new_type = st.radio("Type", ["Individual", "Company"], horizontal=True, key="new_c_type")
        is_company = new_type == "Company"
        if is_company:
            c1, c2 = st.columns(2)
            new_company_name = c1.text_input("Company name", key="new_c_company_name")
            new_siren = c2.text_input("SIREN", key="new_c_siren")
        else:
            new_company_name = ""
            new_siren = ""
        save_key = st.text_input("Reference name", value=new_company_name, key="new_c_save_key")
        new_email = st.text_input("Email", key="new_c_email")
        c1, c2 = st.columns(2)
        new_phone = c1.text_input("Phone", key="new_c_phone")
        new_website = c2.text_input("Website", key="new_c_website")
        st.markdown("**Address**")
        new_addr = _address_form("new_client", {})
        if st.button("Save client", key="save_new_c_btn"):
            entry = {
                "type": "company" if is_company else "individual",
                "name": save_key, "email": new_email,
                "phone": new_phone or None, "website": new_website or None,
                "address": new_addr,
            }
            if is_company:
                entry["company_name"] = new_company_name
                entry["siren"] = new_siren
            profile_store.save_client(save_key, entry)
            st.success(f"Client '{save_key}' saved.")
            st.rerun()


# ---------------------------------------------------------------------------
# Tab 3: Sender Profile
# ---------------------------------------------------------------------------

def _tab_sender():
    s = profile_store.load_sender() or {}
    if not s:
        st.info("No sender profile saved yet. Fill in the fields below and click Save.")

    siren = st.text_input("SIREN", value=s.get("siren", ""), key="sp_siren")
    company = st.text_input("Company name", value=s.get("company", ""), key="sp_company")
    name = st.text_input("Contact name", value=s.get("name", ""), key="sp_name")
    email = st.text_input("Email", value=s.get("email", ""), key="sp_email")
    c1, c2 = st.columns(2)
    phone = c1.text_input("Phone", value=s.get("phone", "") or "", key="sp_phone")
    website = c2.text_input("Website", value=s.get("website", "") or "", key="sp_website")
    st.markdown("**Address**")
    addr = _address_form("sp", s.get("address", {}))

    if st.button("Save sender profile", type="primary", key="save_sp_btn"):
        profile_store.save_sender({
            "siren": siren, "company": company, "name": name,
            "email": email, "phone": phone or None, "website": website or None,
            "address": addr,
        })
        st.success("Sender profile saved.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="KSC Invoicing", layout="wide")
    st.title("KSC Invoicing")
    _init_state()

    tab1, tab2, tab3 = st.tabs(["Generate Invoice", "Manage Clients", "Sender Profile"])

    with tab1:
        _tab_generate()
    with tab2:
        _tab_clients()
    with tab3:
        _tab_sender()


if __name__ == "__main__":
    main()
