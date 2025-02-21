# scraper/main.py

import os
import logging
import re
import time
import json
import csv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError

from scraper.db import SessionLocal, init_db
from scraper.models import Agent
from scraper.config import CHROME_OPTIONS, CHROMIUM_OPTIONS, FIREFOX_OPTIONS

from dotenv import load_dotenv
load_dotenv()  # This will read variables from .env into os.environ

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

def get_driver():
    """
    Create a Selenium WebDriver instance based on environment variable BROWSER.
    Default: chromium.
    """
    browser_choice = os.environ.get('BROWSER', 'chromium').lower()

    if browser_choice == 'chrome':
        logger.info("Using Chrome browser.")
        options = ChromeOptions()
        for arg in CHROME_OPTIONS:
            options.add_argument(arg)
        return webdriver.Chrome(options=options)

    elif browser_choice == 'chromium':
        logger.info("Using Chromium browser.")
        options = ChromeOptions()
        for arg in CHROMIUM_OPTIONS:
            options.add_argument(arg)
        # If needed, specify a custom path:
        # options.binary_location = "/usr/bin/chromium"
        return webdriver.Chrome(options=options)

    elif browser_choice == 'firefox':
        logger.info("Using Firefox browser.")
        options = FirefoxOptions()
        for arg in FIREFOX_OPTIONS:
            options.add_argument(arg)
        return webdriver.Firefox(options=options)

    else:
        logger.warning(f"Browser '{browser_choice}' not recognized; defaulting to Chromium.")
        options = ChromeOptions()
        for arg in CHROMIUM_OPTIONS:
            options.add_argument(arg)
        return webdriver.Chrome(options=options)

def parse_rating(rating_str):
    """
    Remove 'T' and convert to float.
    If rating_str == 'N/A' or cannot be parsed, return None.
    Example: 'T0' -> 0.0, 'T1.5' -> 1.5
    """
    rating_str = rating_str.strip().upper()
    if rating_str.startswith('T'):
        rating_str = rating_str[1:]  # Remove 'T'

    if rating_str == 'N/A' or not rating_str:
        return None

    try:
        return float(rating_str)
    except ValueError:
        logger.debug(f"Could not parse rating: {rating_str}")
        return None

def scrape_zzz_agents():
    """
    Scrapes ZZZ agent data from an environment-defined URL or default.
    Returns a list of dicts containing scraped character data.
    """
    url = os.environ.get('SCRAPE_URL', 'https://www.prydwen.gg/zenless/characters/')
    limit_str = os.environ.get('SCRAPE_LIMIT', None)

    if limit_str == "None" or not limit_str:
        limit = None
    else:
        try:
            limit = int(limit_str)
        except ValueError:
            logger.error(f"Invalid SCRAPE_LIMIT value: {limit_str}. Must be int or None.")
            limit = None

    driver = get_driver()

    agents = []
    logger.info(f"Scraping from URL: {url}; limit={limit or 'No Limit'}")

    try:
        driver.get(url)

        # Wait until the avatar cards appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "avatar-card"))
        )
        character_cards = driver.find_elements(By.CLASS_NAME, "avatar-card")

        actions = ActionChains(driver)
        possible_roles = ['DPS', 'Stun', 'Support']

        # If limit is not None, slice the list
        if limit is not None:
            character_cards = character_cards[:limit]

        # Let Tippy fully initialize
        time.sleep(2)

        for card in character_cards:
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)

            # Hover to trigger popover
            actions.move_to_element(card).perform()

            # Wait until the popover ('tippy-content') is visible
            try:
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'tippy-content'))
                )
            except:
                logger.warning("Popover not found or took too long to appear.")
                continue

            # Once visible, parse
            try:
                popover_content = driver.find_element(By.CLASS_NAME, "tippy-content")
                soup = BeautifulSoup(popover_content.get_attribute('innerHTML'), 'html.parser')
                images = soup.find_all('img')

                # Guard against missing images
                # name=images[1], attribute=7, specialty=10, faction=13 
                # but these indexes may not exist for new/placeholder characters
                name = images[1]['alt'] if len(images) > 1 else "Unknown"
                attribute = images[7]['alt'] if len(images) > 7 else "Unknown"
                specialty = images[10]['alt'] if len(images) > 10 else "Unknown"
                faction = images[13]['alt'] if len(images) > 13 else "Unknown"

                # Rank
                if soup.find(class_='rar-A'):
                    rank = 'A'
                elif soup.find(class_='rar-S'):
                    rank = 'S'
                else:
                    rank = 'Unknown'

                # Determine role from text
                text_content = soup.get_text(separator=' ')
                role = 'Unknown'
                for r in possible_roles:
                    if r in text_content:
                        role = r
                        break

                # Now handle rating divs
                rating_divs = soup.find_all('div', class_=re.compile(r'rating-hsr-\d+'))

                # Defaults if no rating found
                sd_str = 'N/A'
                da_str = 'N/A'

                # If there's at least one rating, assume it's SD
                if len(rating_divs) > 0:
                    sd_str = rating_divs[0].get_text(strip=True)

                # If there's a second rating, assume it's DA
                if len(rating_divs) > 1:
                    da_str = rating_divs[1].get_text(strip=True)

                # Convert to floats
                sd_val = parse_rating(sd_str)
                da_val = parse_rating(da_str)

                numeric_ratings = [r for r in (sd_val, da_val) if r is not None]
                if numeric_ratings:
                    avg_rating = round(sum(numeric_ratings) / len(numeric_ratings), 2)
                else:
                    avg_rating = None

                agents.append({
                    'name': name,
                    'rank': rank,
                    'attribute': attribute,
                    'specialty': specialty,
                    'faction': faction,
                    'role': role,
                    'sd_rating': sd_val,
                    'da_rating': da_val,
                    'average_rating': avg_rating
                })

                logger.info(f"Scraped: {name} (avg_rating={avg_rating})")

            except Exception as e:
                logger.error(f"Error processing popover: {e}", exc_info=True)

    finally:
        driver.quit()

    return agents

def save_agents_to_db(agents):
    """
    Persists scraped agent data into the database.
    If an agent already exists, update its ratings (and average) if changed.
    """
    db = SessionLocal()
    try:
        for data in agents:
            existing = db.query(Agent).filter_by(name=data['name']).first()
            if existing:
                # Check if the new ratings differ
                updated = False
                if existing.sd_rating != data['sd_rating']:
                    existing.sd_rating = data['sd_rating']
                    updated = True
                if existing.da_rating != data['da_rating']:
                    existing.da_rating = data['da_rating']
                    updated = True
                if existing.average_rating != data['average_rating']:
                    existing.average_rating = data['average_rating']
                    updated = True

                if updated:
                    db.commit()
                    logger.info(f"Updated ratings for {existing.name}")
                else:
                    logger.info(f"No rating changes for {existing.name}, skipping update.")
            else:
                # New agent
                ag = Agent(
                    name=data['name'],
                    rank=data['rank'],
                    attribute=data['attribute'],
                    specialty=data['specialty'],
                    faction=data['faction'],
                    role=data['role'],
                    sd_rating=data['sd_rating'],
                    da_rating=data['da_rating'],
                    average_rating=data['average_rating']
                )

                db.add(ag)
                try:
                    db.commit()
                    logger.info(f"Saved {ag.name} to DB.")
                except IntegrityError:
                    db.rollback()
                    logger.warning(f"Agent '{ag.name}' caused IntegrityError, skipping...")

    finally:
        db.close()

def get_agents():
    db = SessionLocal()
    try:
        all_agents = db.query(Agent).all()
        return all_agents
    finally:
        db.close()

def export_agents_json(agents, filename="agents_export.json"):
    data = []
    for ag in agents:
        data.append({
            "name": ag.name,
            "rank": ag.rank,
            "attribute": ag.attribute,
            "specialty": ag.specialty,
            "faction": ag.faction,
            "role": ag.role,
            "sd_rating": ag.sd_rating,
            "da_rating": ag.da_rating,
            "average_rating": ag.average_rating
        })

    os.makedirs("data_exports", exist_ok=True)
    with open(os.path.join("data_exports", filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Exported {len(data)} records to {filename} successfully!")

def export_agents_csv(agents, filename="agents_export.csv"):
    os.makedirs("data_exports", exist_ok=True)
    with open(os.path.join("data_exports", filename), "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "name", "rank", "attribute", "specialty", "faction", "role",
            "sd_rating", "da_rating", "average_rating"
        ])
        for ag in agents:
            writer.writerow([
                ag.name,
                ag.rank,
                ag.attribute,
                ag.specialty,
                ag.faction,
                ag.role,
                ag.sd_rating,
                ag.da_rating,
                ag.average_rating
            ])
    print(f"Exported {len(agents)} records to {filename} successfully!")

def main():
    # Initialize/ensure DB structure
    init_db()
    logger.info("Database initialized.")

    # Scrape
    agents = scrape_zzz_agents()
    if agents:
        save_agents_to_db(agents)
        logger.info("All agents saved or updated in DB.")

    logger.info("Scraping process completed.")

    # Query all agents in DB
    all_agents = get_agents()

    # Export
    export_agents_json(all_agents, "agents.json")
    export_agents_csv(all_agents, "agents.csv")

if __name__ == "__main__":
    main()