#!/usr/bin/env python3
import argparse
import csv
import json
import os
import random
from datetime import date, timedelta
from typing import Dict, List, Any


OUTPUT_JSON = "/Users/localuser/msa/mock_data/mock_dataset.json"
OUTPUT_CSV = "/Users/localuser/msa/mock_data/mock_dataset.csv"


def ensure_dirs() -> None:
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)


def random_date(start_year: int = 1990, end_year: int = 2023) -> str:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta_days = (end - start).days
    chosen = start + timedelta(days=random.randint(0, delta_days))
    return chosen.isoformat()


def build_record(record_id: int) -> Dict[str, Any]:
    states = [
        "CA","NY","TX","FL","WA","IL","AZ","CO","NJ","MA",
        "PA","GA","NC","VA","OH","MI","MN","OR","MD","TN"
    ]
    first_names = [
        "Alex","Jordan","Taylor","Casey","Riley","Morgan","Avery","Quinn","Jamie","Cameron",
        "Logan","Reese","Rowan","Drew","Elliot","Harper","Parker","Sage","Skyler","Finley"
    ]
    last_names = [
        "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
        "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"
    ]

    client_first = random.choice(first_names)
    client_last = random.choice(last_names)
    opposing_first = random.choice(first_names)
    opposing_last = random.choice(last_names)

    children_present = random.choice([True, False])
    domestic_violence = random.choices([True, False], weights=[1, 9])[0]
    business_ownership = random.choice([True, False])
    retirement_accounts = random.choice([True, False])
    spousal_support_sought = random.choice([True, False])
    high_net_worth = random.choices([True, False], weights=[2, 8])[0]

    client_income = round(random.uniform(2500, 30000 if high_net_worth else 15000), 2)
    opposing_income = round(random.uniform(2500, 30000 if high_net_worth else 15000), 2)

    community_assets: List[Dict[str, Any]] = []
    # Real property
    community_assets.append({
        "name": "Primary Residence",
        "type": "real_property",
        "value": round(random.uniform(150000, 2500000 if high_net_worth else 1100000), 2),
        "valuation_date": random_date(2022, 2025),
        "is_marital": True,
        "basis": round(random.uniform(100000, 900000), 2),
        "lien_balance": round(random.uniform(30000, 1500000), 2),
        "address": {
            "street": f"{random.randint(100, 9999)} Example St",
            "city": "Sample City",
            "state": random.choice(states),
            "zip": f"{random.randint(90000, 96999)}"
        }
    })
    # Vehicles
    community_assets.append({
        "name": "Vehicles",
        "type": "vehicle",
        "value": round(random.uniform(5000, 120000), 2),
        "is_marital": True,
        "lien_balance": round(random.uniform(0, 40000), 2)
    })
    # Business
    if business_ownership:
        community_assets.append({
            "name": "Business Equity",
            "type": "business",
            "value": round(random.uniform(20000, 2500000 if high_net_worth else 500000), 2),
            "is_marital": True,
            "valuation_date": random_date(2021, 2025),
            "notes": "Estimated by simplified income approach"
        })
    # Retirement
    if retirement_accounts:
        community_assets.append({
            "name": "Retirement Accounts",
            "type": "retirement",
            "account_type": random.choice(["401k", "IRA", "403b", "Pension"]),
            "institution": random.choice(["Vanguard", "Fidelity", "Schwab", "TIAA"]),
            "value": round(random.uniform(10000, 1500000 if high_net_worth else 400000), 2),
            "is_marital": True,
            "needs_qdro": True
        })

    debts: List[Dict[str, Any]] = [
        {
            "name": "Mortgage",
            "creditor": "Sample Bank, N.A.",
            "type": "mortgage",
            "balance": round(random.uniform(50000, 1500000), 2),
            "interest_rate": round(random.uniform(2.75, 8.25), 2),
            "min_payment": round(random.uniform(800, 4500), 2),
            "is_joint": True
        },
        {
            "name": "Credit Cards",
            "creditor": "Sample Card Co",
            "type": "revolving",
            "balance": round(random.uniform(2000, 45000), 2),
            "interest_rate": round(random.uniform(10.0, 29.99), 2),
            "min_payment": round(random.uniform(50, 600), 2),
            "is_joint": random.choice([True, False])
        }
    ]

    children_count = random.randint(1, 4) if children_present else 0

    record: Dict[str, Any] = {
        "id": f"mock-{record_id:03d}",
        "jurisdiction_state": random.choice(states),
        "marriage_date": random_date(1990, 2018),
        "date_of_separation": random_date(2010, 2025),
        "client_first_name": client_first,
        "client_last_name": client_last,
        "opposing_first_name": opposing_first,
        "opposing_last_name": opposing_last,
        "children_present": children_present,
        "children_count": children_count,
        "domestic_violence_factors": domestic_violence,
        "business_ownership": business_ownership,
        "retirement_accounts_present": retirement_accounts,
        "spousal_support_sought": spousal_support_sought,
        "high_net_worth": high_net_worth,
        "client_gross_monthly_income": client_income,
        "opposing_gross_monthly_income": opposing_income,
        "community_property_assets": community_assets,
        "debts": debts,
        "retirement_accounts": [
            {
                "plan_type": random.choice(["401k", "Pension", "IRA"]),
                "institution": random.choice(["Vanguard", "Fidelity", "Schwab"]),
                "estimated_balance": round(random.uniform(5000, 750000), 2),
                "needs_qdro": True
            }
        ] if retirement_accounts else [],
        "real_properties": [
            {
                "address": {
                    "street": f"{random.randint(100, 9999)} Oak Ave",
                    "city": "Sample City",
                    "state": random.choice(states),
                    "zip": f"{random.randint(90000, 96999)}"
                },
                "est_value": round(random.uniform(150000, 1500000), 2),
                "mortgage_balance": round(random.uniform(30000, 900000), 2)
            }
        ],
        "spousal_support": {
            "sought": spousal_support_sought,
            "duration_months": random.choice([0, 12, 24, 36, 60]) if spousal_support_sought else 0,
            "reserve": spousal_support_sought
        },
        "child_support_extras": [
            {"type": "childcare", "estimated_monthly": round(random.uniform(0, 1200), 2)},
            {"type": "healthcare_uninsured", "estimated_monthly": round(random.uniform(0, 300), 2)},
            {"type": "special_needs", "estimated_monthly": round(random.uniform(0, 800), 2)}
        ] if children_present else [],
        "parenting_plan": {
            "schedule": random.choice(["2-2-5-5", "week-on/week-off", "3-4-4-3"]),
            "holidays": "Alternating odd/even years",
            "decision_making": random.choice(["joint", "sole" ]),
            "exchanges": random.choice(["School exchanges", "Police station", "At residence"])
        } if children_present else {},
        "health_insurance": {
            "provider": random.choice(["BlueCross", "Kaiser", "Aetna", "United"]),
            "monthly_premium": round(random.uniform(200, 1200), 2)
        },
        "tax": {
            "filing_status": random.choice(["single", "married_separate", "head_of_household"]),
            "dependency_claiming": random.choice(["alternate_years", "petitioner", "respondent"]) if children_present else "n/a"
        },
        "equalization_payment": round(random.uniform(0, 50000), 2),
        "use_case_tags": [
            "kids" if children_present else "no_kids",
            "business" if business_ownership else "no_business",
            "retirement" if retirement_accounts else "no_retirement",
            "spousal_support" if spousal_support_sought else "no_spousal_support",
            "dv" if domestic_violence else "no_dv",
            "hnw" if high_net_worth else "non_hnw"
        ]
    }
    return record


def write_json(records: List[Dict[str, Any]]) -> None:
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def write_csv(records: List[Dict[str, Any]]) -> None:
    # Flatten a subset; keep arrays as JSON strings for CSV
    fieldnames = [
        "id","jurisdiction_state","marriage_date","date_of_separation",
        "client_first_name","client_last_name","opposing_first_name","opposing_last_name",
        "children_present","children_count","domestic_violence_factors","business_ownership",
        "retirement_accounts_present","spousal_support_sought","high_net_worth",
        "client_gross_monthly_income","opposing_gross_monthly_income",
        "community_property_assets","debts","use_case_tags"
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            row = {**{k: r.get(k) for k in fieldnames}}
            # Convert complex types to JSON strings
            for k in ["community_property_assets", "debts", "use_case_tags"]:
                row[k] = json.dumps(r.get(k, []))
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate anonymized mock MSA dataset")
    parser.add_argument("--count", type=int, default=50, help="Number of records to generate (>=50)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.count < 50:
        raise SystemExit("--count must be at least 50 to satisfy acceptance criteria")

    random.seed(args.seed)
    ensure_dirs()

    records = [build_record(i + 1) for i in range(args.count)]
    write_json(records)
    write_csv(records)
    print(f"Generated {len(records)} records:\n- {OUTPUT_JSON}\n- {OUTPUT_CSV}")


if __name__ == "__main__":
    main()


