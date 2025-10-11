#!/usr/bin/env python3
import argparse
import json
import os
from typing import Dict


ROOT = "/Users/localuser/msa"
MOCK_JSON = os.path.join(ROOT, "mock_data/mock_dataset.json")
TPL_WITH = os.path.join(ROOT, "templates/florida/msa_with_children.md")
TPL_NO = os.path.join(ROOT, "templates/florida/msa_no_children.md")
OUT_DIR = os.path.join(ROOT, "drafts/florida")


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def render(template: str, ctx: Dict[str, str]) -> str:
    text = template
    for k, v in ctx.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def load_clause(rel_path: str) -> str:
    path = os.path.join(ROOT, rel_path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def build_attachments(record: Dict) -> str:
    lines = []
    # Attachment A - Assets
    lines.append("\n\n## Attachment A — Assets\n")
    assets = record.get("community_property_assets", [])
    if assets:
        for a in assets:
            lines.append(f"- {a.get('name')}: ${a.get('value', 0)}")
    else:
        lines.append("- None disclosed")
    # Attachment B - Debts
    lines.append("\n\n## Attachment B — Debts\n")
    debts = record.get("debts", [])
    if debts:
        for d in debts:
            lines.append(f"- {d.get('name')}: ${d.get('balance', 0)}")
    else:
        lines.append("- None disclosed")
    # Financial Summary
    lines.append("\n\n## Attachment C — Financial Summary\n")
    lines.append(f"- Client gross monthly income: ${record.get('client_gross_monthly_income', 0)}")
    lines.append(f"- Opposing gross monthly income: ${record.get('opposing_gross_monthly_income', 0)}")
    # Parenting Plan Summary (if applicable)
    if record.get('children_present', False):
        lines.append("\n\n## Attachment D — Parenting Plan Summary\n")
        lines.append("- See Parenting Plan (Form 12.995) for detailed terms.")
    return "\n".join(lines)


def choose_spousal_clause(spousal_support_sought: bool) -> str:
    if spousal_support_sought:
        return "Reserved for further determination consistent with statutory factors."
    return "Waived by both parties."


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Florida MSA drafts from mock data")
    parser.add_argument("--index_with_children", type=int, default=0, help="Mock record index for with-children template")
    parser.add_argument("--index_no_children", type=int, default=1, help="Mock record index for no-children template")
    args = parser.parse_args()

    records = json.loads(read(MOCK_JSON))
    tpl_with = read(TPL_WITH)
    tpl_no = read(TPL_NO)

    def ctx_from_record(r: Dict) -> Dict[str, str]:
        spousal_clause = load_clause(
            "templates/clauses/florida/spousal_support/reserved.md" if r.get("spousal_support_sought", False)
            else "templates/clauses/florida/spousal_support/waived.md"
        )
        property_clause = load_clause("templates/clauses/florida/property/division.md")
        child_support_clause = load_clause("templates/clauses/florida/child_support/guidelines.md")
        parenting_plan_clause = load_clause("templates/clauses/florida/parenting/plan_ref.md")
        retirement_clause = load_clause("templates/clauses/florida/retirement/qdro.md")
        return {
            "client_first_name": r.get("client_first_name", "Client"),
            "client_last_name": r.get("client_last_name", "Name"),
            "opposing_first_name": r.get("opposing_first_name", "Opposing"),
            "opposing_last_name": r.get("opposing_last_name", "Party"),
            "marriage_date": r.get("marriage_date", ""),
            "date_of_separation": r.get("date_of_separation", ""),
            "spousal_support_clause": spousal_clause,
            "property_clause": property_clause,
            "child_support_clause": child_support_clause,
            "parenting_plan_clause": parenting_plan_clause,
            "retirement_clause": retirement_clause,
        }

    r_with = records[args.index_with_children]
    r_no = records[args.index_no_children]

    ctx_with = ctx_from_record(r_with)
    ctx_no = ctx_from_record(r_no)
    draft_with = render(tpl_with, ctx_with) + build_attachments(r_with)
    draft_no = render(tpl_no, ctx_no) + build_attachments(r_no)

    out_with = os.path.join(OUT_DIR, f"msa_with_children_{args.index_with_children:03d}.md")
    out_no = os.path.join(OUT_DIR, f"msa_no_children_{args.index_no_children:03d}.md")
    write(out_with, draft_with)
    write(out_no, draft_no)
    print(f"Wrote:\n- {out_with}\n- {out_no}")


if __name__ == "__main__":
    main()


