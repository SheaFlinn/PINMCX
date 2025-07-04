import pytest
from unittest.mock import patch
from contract_chain import scrape_headlines, filter_headlines, reframe_headlines

# Mock sample data for tests
SAMPLE_CITY = "Memphis"
SAMPLE_HEADLINES = [
    "City Council approves budget",
    "Grizzlies win playoff game",
    "Mayor announces new park",
    "City Council approves budget"  # Duplicate for deduplication test
]

# 1. scrape_headlines

def test_scrape_headlines_returns_list():
    result = scrape_headlines(SAMPLE_CITY)
    assert isinstance(result, list)
    # TODO: Integration test with real scraper/API

# 2. filter_headlines

def test_filter_headlines_removes_irrelevant():
    filtered = filter_headlines(SAMPLE_HEADLINES)
    assert isinstance(filtered, list)
    # Should deduplicate
    assert len(filtered) <= len(SAMPLE_HEADLINES)
    # TODO: Integration test with real civic filtering

# 3. reframe_headlines

def test_reframe_headlines_formats_questions():
    reframed = reframe_headlines(["City Council approves budget"])
    assert isinstance(reframed, list)
    assert all(isinstance(q, str) for q in reframed)
    # Should reframe to question format
    assert any(q.endswith('?') for q in reframed)
    # TODO: Integration test with real question logic

# 4. refine_spread
from contract_chain import refine_spread

def test_refine_spread_generates_contract():
    contract = refine_spread("Will the City approve the budget?")
    assert isinstance(contract, dict)
    assert contract["outcomes"] == ["Yes", "No"]
    assert "council" in contract["resolution_criteria"].lower()
    assert contract["deadline"]

def test_patch_contract_adds_metadata():
    from contract_chain import patch_contract
    contract = {
        "question": "Will the City Council approve $8M for stormwater bonds?",
        "outcomes": ["Yes", "No"],
        "resolution_criteria": "Public vote results",
        "deadline": "2024-08-30"
    }
    patched = patch_contract(contract.copy())
    assert "xp_weight" in patched and patched["xp_weight"] == 1.0
    assert "initial_odds" in patched and patched["initial_odds"] == 0.5
    assert "liquidity_cap" in patched and patched["liquidity_cap"] > 0
    assert "city" in patched and isinstance(patched["city"], str)
    assert "created_at" in patched
    from datetime import datetime
    # Check ISO format
    try:
        datetime.fromisoformat(patched["created_at"])
    except Exception:
        assert False, "created_at is not a valid ISO timestamp"
    assert patched["question"] == contract["question"]
    assert patched["deadline"] == contract["deadline"]
    assert patched["outcomes"] == contract["outcomes"]
    assert patched["resolution_criteria"] == contract["resolution_criteria"]

def test_validate_contract_success_and_failure():
    from contract_chain import validate_contract
    from datetime import datetime
    # Valid contract (should pass)
    valid_contract = {
        "question": "Will the City Council approve $8M for stormwater bonds?",
        "outcomes": ["Yes", "No"],
        "resolution_criteria": "Public vote results",
        "deadline": "2024-08-30",
        "city": "memphis",
        "xp_weight": 1.0,
        "initial_odds": 0.5,
        "liquidity_cap": 1000,
        "created_at": datetime.utcnow().isoformat(),
        "source": "auto"
    }
    assert validate_contract(valid_contract) is True

    # Missing field (should fail)
    missing_field_contract = valid_contract.copy()
    del missing_field_contract["xp_weight"]
    assert validate_contract(missing_field_contract) is False

    # Invalid odds (should fail)
    invalid_odds_contract = valid_contract.copy()
    invalid_odds_contract["initial_odds"] = 1.5
    assert validate_contract(invalid_odds_contract) is False

    # Invalid outcomes (should fail)
    invalid_outcomes_contract = valid_contract.copy()
    invalid_outcomes_contract["outcomes"] = ["Yes"]
    assert validate_contract(invalid_outcomes_contract) is False
    invalid_outcomes_contract2 = valid_contract.copy()
    invalid_outcomes_contract2["outcomes"] = "Yes"
    assert validate_contract(invalid_outcomes_contract2) is False

# Space for future integration tests with DB/models
