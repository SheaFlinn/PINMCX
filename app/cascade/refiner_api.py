def refine_question_with_scope(draft: dict) -> dict:
    """
    Stage 3 of the Cascade: Adds clarity to the contract by identifying key actors, scope, and timeline.
    Updates 'actor', 'scope', 'timeline', and appends to stage_log.
    """

    title = draft.get("refined_title") or draft.get("title")
    city = draft.get("city", "")

    # Placeholder logic — will be replaced by AI call
    actor = f"{city} City Council"
    scope = f"Formal decisions or votes relevant to: '{title}'"
    timeline = "within the next 90 days"

    log_entry = {
        "stage": "refiner",
        "input": title,
        "output": {
            "actor": actor,
            "scope": scope,
            "timeline": timeline
        },
        "verdict": "pending"
    }

    draft["actor"] = actor
    draft["scope"] = scope
    draft["timeline"] = timeline
    draft.setdefault("stage_log", []).append(log_entry)
    return draft
