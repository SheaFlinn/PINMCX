import pytest
from unittest.mock import patch, MagicMock
import os
import json
import shutil
import tempfile
from pathlib import Path

import scraper

SCRAPER_CONFIGS = 'scraper_configs'

@pytest.fixture(autouse=True)
def temp_scraper_configs_dir(monkeypatch):
    # Create a temporary directory for scraper_configs
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(scraper, 'load_scraper_config', lambda city: _load_config_from_temp(temp_dir, city))
    monkeypatch.setattr('scraper_config_loader.load_scraper_config', lambda city: _load_config_from_temp(temp_dir, city))
    os.makedirs(temp_dir, exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir)

def _write_config(temp_dir, city, config_dict):
    fname = Path(temp_dir) / f"{city.lower()}.json"
    with open(fname, 'w') as f:
        json.dump(config_dict, f)

def _load_config_from_temp(temp_dir, city):
    fname = Path(temp_dir) / f"{city.lower()}.json"
    if not fname.exists():
        raise ValueError(f"No config found for city: {city}")
    with open(fname) as f:
        return json.load(f)

# 1. API Scraper Success
def test_api_scraper_success(temp_scraper_configs_dir):
    config = {
        "type": "api",
        "url": "http://fake.api/civic",
        "headers": {},
    }
    _write_config(temp_scraper_configs_dir, 'testcity_api', config)
    fake_api_response = {"headlines": ["A", "B", "C"]}
    with patch('scraper.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = fake_api_response
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp
        result = scraper.scrape_headlines('testcity_api')
        assert result == ["A", "B", "C"]

# 2. HTML Scraper Success
def test_html_scraper_success(temp_scraper_configs_dir):
    config = {
        "type": "html",
        "url": "http://fake.html/page",
        "selector": ".headline"
    }
    _write_config(temp_scraper_configs_dir, 'testcity_html', config)
    html = '<div class="headline">First</div><div class="headline">Second</div>'
    with patch('scraper.requests.get') as mock_get, \
         patch('scraper.BeautifulSoup') as mock_bs:
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp
        mock_soup = MagicMock()
        mock_el1 = MagicMock(); mock_el1.get_text.return_value = "First"
        mock_el2 = MagicMock(); mock_el2.get_text.return_value = "Second"
        mock_soup.select.return_value = [mock_el1, mock_el2]
        mock_bs.return_value = mock_soup
        result = scraper.scrape_headlines('testcity_html')
        assert result == ["First", "Second"]

# 3. Missing Config
def test_missing_config(temp_scraper_configs_dir):
    with pytest.raises(ValueError) as exc:
        scraper.scrape_headlines('nonexistent_city')
    assert "No config found" in str(exc.value)

# 4. Malformed Config
def test_malformed_config(temp_scraper_configs_dir):
    config = {"type": "api"}  # missing 'url'
    _write_config(temp_scraper_configs_dir, 'malformed_city', config)
    with pytest.raises(ValueError) as exc:
        scraper.scrape_headlines('malformed_city')
    assert "Malformed config" in str(exc.value)

# 5. Invalid Response / Parsing Fails
def test_invalid_response_returns_empty(temp_scraper_configs_dir, caplog):
    config = {"type": "api", "url": "http://fake.api/civic"}
    _write_config(temp_scraper_configs_dir, 'testcity_api', config)
    with patch('scraper.requests.get') as mock_get, caplog.at_level('ERROR'):
        mock_resp = MagicMock()
        mock_resp.json.side_effect = Exception("fail")
        mock_resp.raise_for_status = lambda: None
        mock_get.return_value = mock_resp
        result = scraper.scrape_headlines('testcity_api')
        assert result == []
        assert "Error during scraping/parsing for city 'testcity_api'" in caplog.text

# Note: All network and config access is patched/mocked; no live internet or real file system is touched.
