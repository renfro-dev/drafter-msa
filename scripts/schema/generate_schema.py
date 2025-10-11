1#!/usr/bin/env python3
import csv
import json
import os
from typing import List, Dict, Any


SCHEMA_JSON_PATH = "/Users/localuser/msa/intake_schema/hubspot_properties.json"
SCHEMA_CSV_PATH = "/Users/localuser/msa/intake_schema/schema.csv"


def ensure_dirs() -> None:
    os.makedirs(os.path.dirname(SCHEMA_JSON_PATH), exist_ok=True)


def hubspot_properties() -> List[Dict[str, Any]]:
    # Minimal, extensible set covering categories in PRD. Additions welcome.
    properties: List[Dict[str, Any]] = [
        # Basic information
        {"name": "client_first_name", "label": "Client First Name", "type": "string", "fieldType": "text", "groupName": "basic_information", "description": "Given name of client."},
        {"name": "client_last_name", "label": "Client Last Name", "type": "string", "fieldType": "text", "groupName": "basic_information", "description": "Family name of client."},
        {"name": "client_email", "label": "Client Email", "type": "string", "fieldType": "text", "groupName": "basic_information", "description": "Email for communications."},
        {"name": "client_phone", "label": "Client Phone", "type": "string", "fieldType": "text", "groupName": "basic_information", "description": "Primary phone number."},
        {"name": "client_address", "label": "Client Address", "type": "string", "fieldType": "textarea", "groupName": "basic_information", "description": "Street, city, state, ZIP."},
        {"name": "jurisdiction_state", "label": "Jurisdiction State", "type": "enumeration", "fieldType": "select", "groupName": "basic_information", "options": [
            {"label": s, "value": s} for s in [
                "CA","NY","TX","FL","WA","IL","AZ","CO","NJ","MA","PA","GA","NC","VA","OH","MI","MN","OR","MD","TN"
            ]
        ], "description": "State governing the MSA."},

        # Case information
        {"name": "case_number", "label": "Case Number", "type": "string", "fieldType": "text", "groupName": "case_information", "description": "Court case number if assigned."},
        {"name": "filing_county", "label": "Filing County", "type": "string", "fieldType": "text", "groupName": "case_information", "description": "County of filing."},
        {"name": "date_of_separation", "label": "Date of Separation", "type": "date", "fieldType": "date", "groupName": "case_information", "description": "Date of separation for community/separate property analysis."},
        {"name": "marriage_date", "label": "Marriage Date", "type": "date", "fieldType": "date", "groupName": "case_information", "description": "Date of marriage."},
        {"name": "children_present", "label": "Children Present", "type": "bool", "fieldType": "booleancheckbox", "groupName": "case_information", "description": "Whether the parties have minor children."},
        {"name": "domestic_violence_factors", "label": "Domestic Violence Factors", "type": "bool", "fieldType": "booleancheckbox", "groupName": "case_information", "description": "Presence of DV considerations affecting support/custody."},

        # Financial information
        {"name": "client_gross_monthly_income", "label": "Client Gross Monthly Income", "type": "number", "fieldType": "number", "groupName": "financial_information", "description": "Gross monthly income of client in USD."},
        {"name": "opposing_gross_monthly_income", "label": "Opposing Gross Monthly Income", "type": "number", "fieldType": "number", "groupName": "financial_information", "description": "Gross monthly income of opposing party in USD."},
        {"name": "community_property_assets", "label": "Community Property Assets", "type": "string", "fieldType": "textarea", "groupName": "financial_information", "description": "Summary list of community assets with rough values."},
        {"name": "separate_property_assets", "label": "Separate Property Assets", "type": "string", "fieldType": "textarea", "groupName": "financial_information", "description": "Summary list of separate assets with rough values."},
        {"name": "debts_summary", "label": "Debts Summary", "type": "string", "fieldType": "textarea", "groupName": "financial_information", "description": "Community and separate debts with rough balances."},
        {"name": "business_ownership", "label": "Business Ownership Present", "type": "bool", "fieldType": "booleancheckbox", "groupName": "financial_information", "description": "Whether either party owns a business."},
        {"name": "retirement_accounts_present", "label": "Retirement Accounts Present", "type": "bool", "fieldType": "booleancheckbox", "groupName": "financial_information", "description": "Whether retirement accounts exist (QDRO likely)."},
        {"name": "spousal_support_sought", "label": "Spousal Support Sought", "type": "bool", "fieldType": "booleancheckbox", "groupName": "financial_information", "description": "Whether spousal support is requested."},

        # Opposing party information
        {"name": "opposing_first_name", "label": "Opposing First Name", "type": "string", "fieldType": "text", "groupName": "opposing_party_information", "description": "Given name of opposing party."},
        {"name": "opposing_last_name", "label": "Opposing Last Name", "type": "string", "fieldType": "text", "groupName": "opposing_party_information", "description": "Family name of opposing party."},
        {"name": "opposing_email", "label": "Opposing Email", "type": "string", "fieldType": "text", "groupName": "opposing_party_information", "description": "Email of opposing party or counsel."},
        {"name": "opposing_counsel", "label": "Opposing Counsel Name", "type": "string", "fieldType": "text", "groupName": "opposing_party_information", "description": "Name of opposing counsel, if any."},

        # Sensitive information
        {"name": "confidential_terms_notes", "label": "Confidential Terms Notes", "type": "string", "fieldType": "textarea", "groupName": "sensitive_information", "description": "Notes on confidentiality, restraining orders, sealed filings."},
        {"name": "child_custody_parenting_plan_ref", "label": "Parenting Plan Reference", "type": "string", "fieldType": "text", "groupName": "sensitive_information", "description": "Link or ID referencing parenting plan for kids."}
    ]
    return properties


def write_json(properties: List[Dict[str, Any]]) -> None:
    with open(SCHEMA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(properties, f, indent=2)


def write_csv(properties: List[Dict[str, Any]]) -> None:
    fieldnames = ["name", "label", "type", "fieldType", "groupName", "description"]
    with open(SCHEMA_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in properties:
            row = {k: p.get(k, "") for k in fieldnames}
            writer.writerow(row)


def main() -> None:
    ensure_dirs()
    props = hubspot_properties()
    write_json(props)
    write_csv(props)
    print(f"Wrote {len(props)} properties to:\n- {SCHEMA_JSON_PATH}\n- {SCHEMA_CSV_PATH}")


if __name__ == "__main__":
    main()


