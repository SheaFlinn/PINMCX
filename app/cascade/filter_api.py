def filter_contract_quality(draft: dict) -> dict:
    """
    Stage 5 of the Cascade: Filters out contracts that are too vague, biased, or non-falsifiable.
    Adds 'verdict' = accept/reject with reason to stage_log.
    """

    title = draft.get("refined_title", "")
    scope = draft.get("scope", "")
    timeline = draft.get("timeline", "")

    reasons = []

    if not title or len(title) < 15:
        reasons.append("refined_title too short or missing")
    if "?" not in title:
        reasons.append("refined_title is not phrased as a question")
    if "within" not in timeline and "by" not in timeline:
        reasons.append("timeline is not time-bound")
    if "or" in scope and "and" in scope:
        reasons.append("scope may be ambiguous or overbroad")

    verdict = "reject" if reasons else "accept"

    log_entry = {
        "stage": "filter",
        "input": {
            "title": title,
            "scope": scope,
            "timeline": timeline
        },
        "verdict": verdict,
        "reasons": reasons
    }

    draft.setdefault("stage_log", []).append(log_entry)
    draft["status"] = "rejected" if verdict == "reject" else draft.get("status", "draft")
    return draft
