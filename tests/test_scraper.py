# tests/test_scraper.py
import pytest
import os
from scraper.main import scrape_zzz_agents

def test_scrape_zzz_agents():
    """
    Basic test to ensure scraper returns a list and 
    doesn't raise exceptions for the first few characters.
    """
    # Set the environment variable for limit
    os.environ['SCRAPE_LIMIT'] = '3'
    
    agents = scrape_zzz_agents()
    assert isinstance(agents, list), "Scraper should return a list"
    # Check required keys
    for ag in agents:
        assert "name" in ag, "Character entry missing 'name'"
        assert "rank" in ag, "Character entry missing 'rank'"
        assert "attribute" in ag, "Character entry missing 'attribute'"
        assert "specialty" in ag, "Character entry missing 'specialty'"
        assert "faction" in ag, "Character entry missing 'faction'"
        assert "role" in ag, "Character entry missing 'role'"
        assert "sd_rating" in ag, "Character entry missing 'sd_rating'"
        assert "da_rating" in ag, "Character entry missing 'da_rating'"
        assert "average_rating" in ag, "Character entry missing 'average_rating'"