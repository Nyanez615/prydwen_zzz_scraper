# Prydwen Zenless Zone Zero (ZZZ) Scraper

A Python-based scraper for [Prydwen.gg](https://www.prydwen.gg/zenless/characters) to collect ZZZ agent data, including **name**, **rank**, **attribute**, **specialty**, **faction**, and endgame mode **ratings**.

## Features

- Uses **Selenium** (headless browser) to parse data
- Separate columns for **Shiyu Defense (SD)** ratings (float)
- **Environment variables** to control DB path, browser choice, scrape URL, etc.
- Robust **explicit waits** instead of `time.sleep()`
- **Logging** via Python's `logging` module
- GitHub Actions: 
  - **CI** for tests  

## Installation

1. **Clone** this repository:
   
   ```bash
   git clone https://github.com/Nyanez615/prydwen_zzz_scraper.git
   cd prydwen_zzz_scraper
   ```

2. **Create and activate** a virtual environment
   
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   # On Windows, use `venv\Scripts\activate`
   ```
   
3. **Install** dependencies:
   
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Usage

1. **Set environment variables** (optional). If not set, defaults are used.

- `BROWSER`: defaults to `chromium` (also supports chrome, firefox)
- `SCRAPE_URL`: defaults to Prydwen.gg's ZZZ agents' page
- `SCRAPE_LIMIT`: defaults to `None` (i.e., no limit). Set an integer as a string to limit scraped characters
- `DB_URL`: defaults to `sqlite:///zzz.db`
   
   ```bash
   export BROWSER=chromium
   export SCRAPE_URL="https://www.prydwen.gg/zenless/characters"
   export SCRAPE_LIMIT=None
   export DB_URL="sqlite:///zzz.db"  # Or your own DB location
   ```

2. **Run** the scraper: 
   
   ```bash
   python -m scraper.main
   ```

- This initializes the DB (if not existing), launches headless Chrome (or the chosen browser), scrapes all agents, stores them in `zzz.db`, logs progress to the console, and saves/updates records in zzz.db.

## Testing

- We use `pytest` for testing:
   
   ```bash
   pytest
   ```
- The `tests/` folder contains the test files.
- `tests/__init__.py` is just a package marker file (empty or minimal).

## GitHub Actions

### Continuous Integration (CI)
- Defined in `.github/workflows/ci.yml`
- Runs tests on every push or pull request.
- Exports environment variables:

  ```yaml
  env:
    BROWSER: "chromium"
    SCRAPE_URL: "https://www.prydwen.gg/zenless/characters/"
    SCRAPE_LIMIT: ""
    DB_URL: "sqlite:///zzz.db"
  ```

- Sets PYTHONPATH so the code imports properly:
  
  ```yaml
  - name: Set PYTHONPATH
    un: echo "PYTHONPATH=$GITHUB_WORKSPACE" >> $GITHUB_ENV
  ```

## Additional Configuration

- Configuring Browser: For local usage, install the appropriate browser (Chromium, Chrome, or Firefox). See `scraper/config.py` for browser-specific options.
- Production DB: If you need concurrency or a multi-user environment, switch to Postgres or MySQL by setting DB_URL accordingly.
- Logging: Adjust log levels (debug, info, warning, error) to match your needs. You can edit `logging.basicConfig` in `scraper/main.py`.
- Site Changes: If Prydwen.gg changes its HTML layout, you may need to update selectors or logic.

## Contributing 

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
