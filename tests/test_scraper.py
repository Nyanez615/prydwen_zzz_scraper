# tests/test_scraper.py
import pytest
import os
from scraper.main import scrape_star_rail_characters

def test_scrape_star_rail_characters():
    """
    Basic test to ensure scraper returns a list and 
    doesn't raise exceptions for the first few characters.
    """
    # Set the environment variable for limit
    os.environ['SCRAPE_LIMIT'] = '3'
    
    characters = scrape_star_rail_characters()
    assert isinstance(characters, list), "Scraper should return a list"
    # Check required keys
    for char in characters:
        assert "name" in char, "Character entry missing 'name'"
        assert "rarity" in char, "Character entry missing 'rarity'"
        assert "element" in char, "Character entry missing 'element'"
        assert "path" in char, "Character entry missing 'path'"
        assert "role" in char, "Character entry missing 'role'"
        assert "moc_rating" in char, "Character entry missing 'moc_rating'"
        assert "pf_rating" in char, "Character entry missing 'pf_rating'"
        assert "as_rating" in char, "Character entry missing 'as_rating'"
        assert "average_rating" in char, "Character entry missing 'average_rating'"