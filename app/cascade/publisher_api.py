from app import db
from app.models.contract import ContractDraft
from app.models.published_contract import Contract

def publish_contract(draft: dict) -> dict:
    """
    Stage 8 of the Cascade: Final publishing logic.
    If the contract passed filter stage, create a PublishedContract from the draft.
    """

    last_verdicts = [entry.get("verdict") for entry in draft.get("stage_log", [])]
    if "reject" in last_verdicts:
        draft["status"] = "rejected"
        return draft

    published = Contract(
        draft_id=draft.get("id"),
        city=draft.get("city"),
        title=draft.get("refined_title"),
        description=draft.get("scope"),
        actor=draft.get("actor"),
        resolution_method="Admin judgment or public event confirmation",
        source_url="",  # Optional: store origin
        resolution_date=None,
        current_odds_yes=draft.get("current_odds_yes", 0.5),
        current_odds_no=draft.get("current_odds_no", 0.5),
        xp_threshold=draft.get("xp_threshold", 0),
        total_volume_points=0
    )

    db.session.add(published)
    db.session.commit()

    draft["status"] = "published"
    draft.setdefault("stage_log", []).append({
        "stage": "publisher",
        "input": f"ContractDraft id={draft.get('id')}",
        "output": f"Contract id={published.id}",
        "verdict": "published"
    })

    return draft
