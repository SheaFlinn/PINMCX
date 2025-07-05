import os
import json
from flask import current_app
from app import create_app, db
from app.models.contract import ContractDraft

sample_drafts = [
    {
        "title": "Will the City Council approve the 2025 budget by July?",
        "purpose": "Test contract for budget approval.",
        "scope": "City Council budget vote.",
        "terms": {"resolution_source": "council_minutes"}
    },
    {
        "title": "Will the new zoning ordinance pass before September 2025?",
        "purpose": "Test contract for zoning law.",
        "scope": "City zoning ordinance process.",
        "terms": {"resolution_source": "city_ordinances"}
    },
    {
        "title": "Will the mayor sign the police reform bill in 2025?",
        "purpose": "Test contract for police reform.",
        "scope": "Mayor's office and city council actions.",
        "terms": {"resolution_source": "mayor_press_release"}
    }
]

def seed_contract_drafts():
    app = create_app()
    with app.app_context():
        added = 0
        for draft in sample_drafts:
            exists = ContractDraft.query.filter_by(title=draft["title"]).first()
            if not exists:
                new_draft = ContractDraft(
                    title=draft["title"],
                    purpose=draft["purpose"],
                    scope=draft["scope"],
                    terms=json.dumps(draft["terms"])
                )
                db.session.add(new_draft)
                added += 1
        if added:
            db.session.commit()
        count = ContractDraft.query.count()
        print(f"Seeded {added} new drafts. Total ContractDrafts: {count}")

if __name__ == "__main__":
    seed_contract_drafts()
