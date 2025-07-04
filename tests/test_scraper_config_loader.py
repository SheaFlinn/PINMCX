import os
import pytest
from scraper_config_loader import load_scraper_config

def test_load_existing_config():
    """Test loading an existing config file"""
    config = load_scraper_config("memphis")
    assert config["city"] == "Memphis"
    assert len(config["sources"]) == 2
    assert config["sources"][0]["name"] == "Daily Memphian"

def test_load_nonexistent_config():
    """Test loading a non-existent config file"""
    with pytest.raises(ValueError):
        load_scraper_config("nonexistentcity")

def test_invalid_json_config():
    """Test loading a config file with invalid JSON"""
    # Create a temporary invalid JSON file
    test_dir = "scraper_configs"
    test_file = os.path.join(test_dir, "invalid_json_config.json")
    
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    with open(test_file, "w") as f:
        f.write("{invalid json}")
    
    with pytest.raises(ValueError):
        load_scraper_config("invalid_json")
    
    # Clean up
    os.remove(test_file)

def test_case_insensitivity():
    """Test that city name is case-insensitive"""
    config = load_scraper_config("MEMPHIS")
    assert config["city"] == "Memphis"
    config = load_scraper_config("MemPhis")
    assert config["city"] == "Memphis"
