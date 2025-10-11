#!/usr/bin/env python3
import json
import os
import time
from datetime import date
from typing import Any, Dict, List

import streamlit as st


ROOT = "/Users/localuser/msa"
INTAKE_DIR = os.path.join(ROOT, "intake/records")
DRAFTS_DIR = os.path.join(ROOT, "drafts/florida")

TPL_WITH = os.path.join(ROOT, "templates/florida/msa_with_children.md")
TPL_NO = os.path.join(ROOT, "templates/florida/msa_no_children.md")

CLAUSES = {
    "spousal_waived": os.path.join(ROOT, "templates/clauses/florida/spousal_support/waived.md"),
    "spousal_reserved": os.path.join(ROOT, "templates/clauses/florida/spousal_support/reserved.md"),
    "property": os.path.join(ROOT, "templates/clauses/florida/property/division.md"),
    "child_support": os.path.join(ROOT, "templates/clauses/florida/child_support/guidelines.md"),
    "parenting": os.path.join(ROOT, "templates/clauses/florida/parenting/plan_ref.md"),
    "retirement": os.path.join(ROOT, "templates/clauses/florida/retirement/qdro.md"),
}


def ensure_dirs() -> None:
    os.makedirs(INTAKE_DIR, exist_ok=True)
    os.makedirs(DRAFTS_DIR, exist_ok=True)


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def render_template(template_text: str, context: Dict[str, Any]) -> str:
    text = template_text
    for k, v in context.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def load_clause(key: str) -> str:
    path = CLAUSES[key]
    if not os.path.exists(path):
        return ""
    return read_file(path).strip()


def build_attachments(record: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("\n\n## Attachment A — Assets\n")
    assets: List[Dict[str, Any]] = record.get("community_property_assets", [])
    if assets:
        lines.append("| Name | Type | Value | Lien Balance | Valuation Date | Marital |")
        lines.append("| --- | --- | ---:| ---:| --- | --- |")
        for a in assets:
            lines.append(
                f"| {a.get('name','')} | {a.get('type','')} | ${a.get('value',0)} | ${a.get('lien_balance', a.get('lienBalance','') or 0)} | {a.get('valuation_date','')} | {a.get('is_marital', True)} |"
            )
    else:
        lines.append("- None disclosed")

    lines.append("\n\n## Attachment B — Debts\n")
    debts: List[Dict[str, Any]] = record.get("debts", [])
    if debts:
        lines.append("| Name | Creditor | Type | Balance | Rate | Min Payment | Joint |")
        lines.append("| --- | --- | --- | ---:| ---:| ---:| --- |")
        for d in debts:
            lines.append(
                f"| {d.get('name','')} | {d.get('creditor','')} | {d.get('type','')} | ${d.get('balance',0)} | {d.get('interest_rate', d.get('interestRate',''))}% | ${d.get('min_payment', d.get('minPayment','') or 0)} | {d.get('is_joint', False)} |"
            )
    else:
        lines.append("- None disclosed")

    lines.append("\n\n## Attachment C — Financial Summary\n")
    lines.append(f"- Client gross monthly income: ${record.get('client_gross_monthly_income', 0)}")
    lines.append(f"- Opposing gross monthly income: ${record.get('opposing_gross_monthly_income', 0)}")
    health = record.get("health_insurance", {})
    if health:
        lines.append(f"- Health insurance provider: {health.get('provider','')} ($ {health.get('monthly_premium',0)} / mo)")
    if record.get("equalization_payment"):
        lines.append(f"- Equalization payment (proposed): ${record.get('equalization_payment')}")

    if record.get("children_present", False):
        lines.append("\n\n## Attachment D — Parenting Plan Summary\n")
        pp = record.get("parenting_plan", {})
        if pp:
            lines.append(f"- Schedule: {pp.get('schedule','')}")
            lines.append(f"- Holidays: {pp.get('holidays','')}")
            lines.append(f"- Decision making: {pp.get('decision_making','')}")
            lines.append(f"- Exchanges: {pp.get('exchanges','')}")
        extras = record.get("child_support_extras", [])
        if extras:
            lines.append("- Child support extras (estimated monthly):")
            for e in extras:
                lines.append(f"  - {e.get('type')}: ${e.get('estimated_monthly',0)}")

    return "\n".join(lines)


def collect_form() -> Dict[str, Any]:
    st.title("Florida MSA Intake Form")
    st.caption("Structured intake with conditional sections; outputs JSON for draft generation.")

    col1, col2 = st.columns(2)
    with col1:
        client_first = st.text_input("Client First Name", "Jordan")
        client_last = st.text_input("Client Last Name", "Martinez")
        client_income = st.number_input("Client Gross Monthly Income", min_value=0.0, value=5000.0, step=100.0)
    with col2:
        opp_first = st.text_input("Opposing First Name", "Riley")
        opp_last = st.text_input("Opposing Last Name", "Anderson")
        opp_income = st.number_input("Opposing Gross Monthly Income", min_value=0.0, value=6000.0, step=100.0)

    col3, col4 = st.columns(2)
    with col3:
        marriage_date = st.date_input("Marriage Date", value=date(2010, 1, 1))
    with col4:
        separation_date = st.date_input("Date of Separation", value=date(2022, 1, 1))

    children_present = st.toggle("Children Present", value=True)
    spousal_support_sought = st.toggle("Spousal Support Sought", value=False)
    retirement_present = st.toggle("Retirement Accounts Present", value=True)

    st.subheader("Assets")
    assets_default = [
        {"name": "Primary Residence", "type": "real_property", "value": 750000, "lienBalance": 300000, "valuation_date": str(date.today()), "is_marital": True},
        {"name": "Vehicles", "type": "vehicle", "value": 35000, "lienBalance": 5000, "is_marital": True},
    ]
    assets = st.data_editor(assets_default, num_rows="dynamic", use_container_width=True, key="assets")

    st.subheader("Debts")
    debts_default = [
        {"name": "Mortgage", "creditor": "Sample Bank", "type": "mortgage", "balance": 300000, "interestRate": 4.0, "minPayment": 1800, "is_joint": True},
        {"name": "Credit Cards", "creditor": "Sample Card", "type": "revolving", "balance": 12000, "interestRate": 18.0, "minPayment": 300, "is_joint": False},
    ]
    debts = st.data_editor(debts_default, num_rows="dynamic", use_container_width=True, key="debts")

    if retirement_present:
        st.subheader("Retirement Accounts")
        retirement_default = [
            {"plan_type": "401k", "institution": "Vanguard", "estimated_balance": 95000, "needs_qdro": True}
        ]
        retirement_accounts = st.data_editor(retirement_default, num_rows="dynamic", use_container_width=True, key="retirement")
    else:
        retirement_accounts = []

    st.subheader("Health Insurance")
    health_col1, health_col2 = st.columns(2)
    with health_col1:
        health_provider = st.text_input("Provider", "BlueCross")
    with health_col2:
        monthly_premium = st.number_input("Monthly Premium", min_value=0.0, value=400.0, step=25.0)

    st.subheader("Taxes")
    filing_status = st.selectbox("Filing Status", ["single", "married_separate", "head_of_household"], index=0)
    dependency_claiming = "n/a"
    if children_present:
        dependency_claiming = st.selectbox("Dependency Claiming", ["alternate_years", "petitioner", "respondent"], index=0)

    equalization_payment = st.number_input("Equalization Payment (proposed)", min_value=0.0, value=0.0, step=500.0)

    parenting_plan = {}
    child_support_extras: List[Dict[str, Any]] = []
    if children_present:
        st.subheader("Parenting Plan")
        pp_col1, pp_col2, pp_col3 = st.columns(3)
        with pp_col1:
            schedule = st.selectbox("Schedule", ["2-2-5-5", "week-on/week-off", "3-4-4-3"], index=0)
        with pp_col2:
            holidays = st.text_input("Holidays", "Alternating odd/even years")
        with pp_col3:
            decision_making = st.selectbox("Decision Making", ["joint", "sole"], index=0)
        exchanges = st.text_input("Exchanges", "School exchanges")
        parenting_plan = {
            "schedule": schedule,
            "holidays": holidays,
            "decision_making": decision_making,
            "exchanges": exchanges,
        }
        st.subheader("Child Support Extras (estimated monthly)")
        extras_default = [
            {"type": "childcare", "estimated_monthly": 600},
            {"type": "healthcare_uninsured", "estimated_monthly": 150},
        ]
        child_support_extras = st.data_editor(extras_default, num_rows="dynamic", use_container_width=True, key="extras")

    with st.expander("Upload Supporting Documents (optional)"):
        uploads = st.file_uploader("Select files", accept_multiple_files=True)
        saved_files: List[str] = []
        if uploads:
            upload_dir = os.path.join(INTAKE_DIR, "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            for f in uploads:
                save_path = os.path.join(upload_dir, f.name)
                with open(save_path, "wb") as out:
                    out.write(f.getbuffer())
                saved_files.append(save_path)
            st.success(f"Saved {len(saved_files)} files to {upload_dir}")

    record: Dict[str, Any] = {
        "id": f"form-{int(time.time())}",
        "jurisdiction_state": "FL",
        "client_first_name": client_first,
        "client_last_name": client_last,
        "opposing_first_name": opp_first,
        "opposing_last_name": opp_last,
        "marriage_date": str(marriage_date),
        "date_of_separation": str(separation_date),
        "children_present": children_present,
        "client_gross_monthly_income": client_income,
        "opposing_gross_monthly_income": opp_income,
        "spousal_support_sought": spousal_support_sought,
        "retirement_accounts_present": retirement_present,
        "community_property_assets": assets,
        "debts": debts,
        "retirement_accounts": retirement_accounts,
        "health_insurance": {"provider": health_provider, "monthly_premium": monthly_premium},
        "tax": {"filing_status": filing_status, "dependency_claiming": dependency_claiming},
        "parenting_plan": parenting_plan,
        "child_support_extras": child_support_extras,
        "equalization_payment": equalization_payment,
    }

    return record


def render_draft(record: Dict[str, Any]) -> str:
    with_children = bool(record.get("children_present", False))
    template_path = TPL_WITH if with_children else TPL_NO
    template = read_file(template_path)
    spousal_clause = load_clause("spousal_reserved") if record.get("spousal_support_sought", False) else load_clause("spousal_waived")
    property_clause = load_clause("property")
    child_support_clause = load_clause("child_support") if with_children else ""
    parenting_clause = load_clause("parenting") if with_children else ""
    retirement_clause = load_clause("retirement")
    ctx = {
        "client_first_name": record.get("client_first_name", "Client"),
        "client_last_name": record.get("client_last_name", "Name"),
        "opposing_first_name": record.get("opposing_first_name", "Opposing"),
        "opposing_last_name": record.get("opposing_last_name", "Party"),
        "marriage_date": record.get("marriage_date", ""),
        "date_of_separation": record.get("date_of_separation", ""),
        "spousal_support_clause": spousal_clause,
        "property_clause": property_clause,
        "child_support_clause": child_support_clause,
        "parenting_plan_clause": parenting_clause,
        "retirement_clause": retirement_clause,
    }
    return render_template(template, ctx) + build_attachments(record)


def main() -> None:
    ensure_dirs()
    record = collect_form()

    colA, colB = st.columns(2)
    with colA:
        if st.button("Save Intake JSON", type="primary"):
            out_path = os.path.join(INTAKE_DIR, f"{record['id']}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)
            st.success(f"Saved: {out_path}")
    with colB:
        if st.button("Render Florida Draft"):
            draft_text = render_draft(record)
            out_path = os.path.join(DRAFTS_DIR, f"{record['id']}.md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(draft_text)
            st.success(f"Draft written: {out_path}")
            st.download_button("Download Draft", data=draft_text.encode("utf-8"), file_name=os.path.basename(out_path), mime="text/markdown")


if __name__ == "__main__":
    main()


