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
from scraper.models import Character
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

def scrape_star_rail_characters():
    """
    Scrapes Star Rail character data from an environment-defined URL or default.
    Returns a list of dicts containing scraped character data.
    """
    url = os.environ.get('SCRAPE_URL', 'https://www.prydwen.gg/star-rail/characters/')
    # If SCRAPE_LIMIT is None or empty, no limit
    limit = os.environ.get('SCRAPE_LIMIT', None)
    
    if limit == "None":
        limit = None
    elif limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            logger.error(f"Invalid SCRAPE_LIMIT value: {limit}. It must be an integer or None.")
            limit = None

    driver = get_driver()

    characters = []
    logger.info(f"Scraping from URL: {url}; limit={limit or 'No Limit'}")

    try:
        driver.get(url)

        # Wait until the avatar cards to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "avatar-card"))
        )
        character_cards = driver.find_elements(By.CLASS_NAME, "avatar-card")

        actions = ActionChains(driver)
        possible_roles = ['Amplifier', 'Support DPS', 'Sustain', 'DPS']

        # If limit is not None, slice the list
        if limit is not None:
            character_cards = character_cards[:limit]

        # After page load:
        time.sleep(2)  # Let Tippy fully initialize

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
                if len(images) < 8:
                    logger.debug("Not enough <img> tags in popover.")
                    continue

                name = images[1]['alt']
                element = images[4]['alt']
                path = images[7]['alt']

                # Rarity
                if soup.find(class_='rar-5'):
                    rarity = '5★'
                elif soup.find(class_='rar-4'):
                    rarity = '4★'
                else:
                    rarity = 'Unknown'

                # Role
                text_content = soup.get_text(separator=' ')
                role = 'Unknown'
                for r in possible_roles:
                    if r in text_content:
                        role = r
                        break

                # Ratings
                rating_divs = soup.find_all('div', class_=re.compile(r'rating-hsr-\d+'))
                moc_str, pf_str, as_str = 'N/A', 'N/A', 'N/A'

                if rating_divs:
                    if rarity == '5★' and len(rating_divs) >= 3:
                        moc_str = rating_divs[0].get_text(strip=True)
                        pf_str = rating_divs[1].get_text(strip=True)
                        as_str = rating_divs[2].get_text(strip=True)
                    elif rarity == '4★' and len(rating_divs) >= 6:
                        moc_str = rating_divs[3].get_text(strip=True)
                        pf_str = rating_divs[4].get_text(strip=True)
                        as_str = rating_divs[5].get_text(strip=True)

                # Convert to floats
                moc_val = parse_rating(moc_str)
                pf_val = parse_rating(pf_str)
                as_val = parse_rating(as_str)

                numeric_ratings = [r for r in (moc_val, pf_val, as_val) if r is not None]
                if numeric_ratings:
                    avg_rating = round(sum(numeric_ratings) / len(numeric_ratings), 2)
                else:
                    avg_rating = None

                characters.append({
                    'name': name,
                    'element': element,
                    'path': path,
                    'rarity': rarity,
                    'role': role,
                    'moc_rating': moc_val,
                    'pf_rating': pf_val,
                    'as_rating': as_val,
                    'average_rating': avg_rating,
                })

                logger.info(f"Scraped: {name} (avg_rating={avg_rating})")

            except Exception as e:
                logger.error(f"Error processing popover: {e}", exc_info=True)

    finally:
        driver.quit()

    return characters

def save_characters_to_db(characters):
    """
    Persists scraped character data into the database.
    If a character already exists, update its ratings (and average) if changed.
    """
    db = SessionLocal()
    try:
        for data in characters:
            existing = db.query(Character).filter_by(name=data['name']).first()
            if existing:
                # Check if the new ratings differ
                updated = False
                if existing.moc_rating != data['moc_rating']:
                    existing.moc_rating = data['moc_rating']
                    updated = True
                if existing.pf_rating != data['pf_rating']:
                    existing.pf_rating = data['pf_rating']
                    updated = True
                if existing.as_rating != data['as_rating']:
                    existing.as_rating = data['as_rating']
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
                # New character
                char = Character(
                    name=data['name'],
                    element=data['element'],
                    path=data['path'],
                    rarity=data['rarity'],
                    role=data['role'],
                    moc_rating=data['moc_rating'],
                    pf_rating=data['pf_rating'],
                    as_rating=data['as_rating'],
                    average_rating=data['average_rating']
                )
                db.add(char)
                try:
                    db.commit()
                    logger.info(f"Saved {char.name} to DB.")
                except IntegrityError:
                    db.rollback()
                    logger.warning(f"Character '{char.name}' caused IntegrityError, skipping...")

    finally:
        db.close()

def get_characters():
    db = SessionLocal()
    try:
        all_chars = db.query(Character).all()
        return all_chars
    finally:
        db.close()

def export_characters_json(characters, filename="characters_export.json"):
    data = []
    for char in characters:
        data.append({
            "name": char.name,
            "element": char.element,
            "path": char.path,
            "rarity": char.rarity,
            "role": char.role,
            "moc_rating": char.moc_rating,
            "pf_rating": char.pf_rating,
            "as_rating": char.as_rating,
            "average_rating": char.average_rating
        })

    os.makedirs("data_exports", exist_ok=True)
    with open(os.path.join("data_exports", filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Exported {len(data)} records to {filename} successfully!")

def export_characters_csv(characters, filename="characters_export.csv"):
    os.makedirs("data_exports", exist_ok=True)
    with open(os.path.join("data_exports", filename), "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "name", "element", "path", "rarity", "role",
            "moc_rating", "pf_rating", "as_rating", "average_rating"
        ])
        for char in characters:
            writer.writerow([
                char.name,
                char.element,
                char.path,
                char.rarity,
                char.role,
                char.moc_rating,
                char.pf_rating,
                char.as_rating,
                char.average_rating
            ])
    print(f"Exported {len(characters)} records to {filename} successfully!")

def main():
    # Initialize/ensure DB structure
    init_db()
    logger.info("Database initialized.")

    # Scrape
    characters = scrape_star_rail_characters()
    if characters:
        save_characters_to_db(characters)
        logger.info("All characters saved or updated in DB.")

    logger.info("Scraping process completed.")

    # Query all characters in DB
    all_chars = get_characters()

    # Export
    export_characters_json(all_chars, "characters.json")
    export_characters_csv(all_chars, "characters.csv")

if __name__ == "__main__":
    main()