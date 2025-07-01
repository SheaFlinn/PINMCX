def reframe_title_as_question(draft: dict) -> dict:
    """
    Stage 2 of the Cascade: Converts the draft's title into a neutral, falsifiable civic forecast question.
    Adds 'refined_title' and updates stage_log.
    """

    original_title = draft.get("title", "")
    city = draft.get("city", "")

    # Placeholder logic; to be replaced by OpenAI/Claude API call
    reframed = f"Will {city} officials take formal action related to: '{original_title}' within the next 90 days?"

    log_entry = {
        "stage": "reframer",
        "input": original_title,
        "output": reframed,
        "verdict": "pending"
    }

    draft["refined_title"] = reframed
    draft.setdefault("stage_log", []).append(log_entry)
    return draft
