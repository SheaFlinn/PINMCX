def patch_bias_and_vagueness(draft: dict) -> dict:
    """
    Stage 4 of the Cascade: Identifies and patches biased or vague language in the contract fields.
    Appends suggested modifications and logs changes with [meta] tags.
    """

    patched_scope = draft.get("scope", "").replace("relevant to", "directly addressing")
    patched_title = draft.get("refined_title", "")
    if "?" not in patched_title:
        patched_title = f"{patched_title}?"

    log_entry = {
        "stage": "patcher",
        "input": {
            "scope": draft.get("scope"),
            "refined_title": draft.get("refined_title")
        },
        "output": {
            "scope": patched_scope,
            "refined_title": patched_title
        },
        "verdict": "patched"
    }

    draft["scope"] = patched_scope
    draft["refined_title"] = patched_title
    draft.setdefault("stage_log", []).append(log_entry)
    return draft
