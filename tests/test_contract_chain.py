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

# Space for future integration tests with DB/models
