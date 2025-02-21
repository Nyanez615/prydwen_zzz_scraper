# Prydwen Honkai: Star Rail Scraper

A Python-based scraper for [Prydwen.gg](https://www.prydwen.gg/star-rail/characters/) to collect Honkai: Star Rail character data, including **numeric ratings** and an **average rating** (rounded to 2 decimals).

## Features

- Uses **Selenium** (headless browser) to parse data
- Separate columns for MoC, PF, and AS ratings (float) plus an **average_rating**
- **Environment variables** to control DB path, browser choice, scrape URL, etc.
- Robust **explicit waits** instead of `time.sleep()`
- **Logging** via Python's `logging` module
- GitHub Actions: 
  - **CI** for tests  
  - **Scheduled** daily run that uploads the latest `hsr.db` artifact

## Installation

1. **Clone** this repository:
   
   ```bash
   git clone https://github.com/YourUsername/star-rail-scraper.git
   cd star-rail-scraper
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
- `SCRAPE_URL`: defaults to Prydwen.gg's Star Rail characters' page
- `SCRAPE_LIMIT`: defaults to `None` (i.e., no limit). Set an integer as a string to limit scraped characters
- `DB_URL`: defaults to `sqlite:///hsr.db`
   
   ```bash
   export BROWSER=chromium
   export SCRAPE_URL="https://www.prydwen.gg/star-rail/characters/"
   export SCRAPE_LIMIT=None
   export DB_URL="sqlite:///hsr.db"  # Or your own DB location
   ```

2. **Run** the scraper: 
   
   ```bash
   python -m scraper.main
   ```

- This initializes the DB (if not existing), launches headless Chrome (or the chosen browser), scrapes all characters, stores them in `hsr.db`, logs progress to the console, and saves/updates records in hsr.db.

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
    SCRAPE_URL: "https://www.prydwen.gg/star-rail/characters/"
    SCRAPE_LIMIT: ""
    DB_URL: "sqlite:///hsr.db"
  ```

- Sets PYTHONPATH so the code imports properly:
  
  ```yaml
  - name: Set PYTHONPATH
    un: echo "PYTHONPATH=$GITHUB_WORKSPACE" >> $GITHUB_ENV
  ```
  
### Scheduled Scraper (Optional): 

- You can create a `.github/workflows/schedule.yml` that runs the scraper daily, then uploads artifacts or the DB. 
- Runs daily at 2 AM UTC, executes `python -m scraper.main`, and uploads `hsr.db`, `characters.json`, and `characters.csv` as artifacts.

## Additional Configuration

- Configuring Browser: For local usage, install the appropriate browser (Chromium, Chrome, or Firefox). See `scraper/config.py` for browser-specific options.
- Production DB: If you need concurrency or a multi-user environment, switch to Postgres or MySQL by setting DB_URL accordingly.
- Logging: Adjust log levels (debug, info, warning, error) to match your needs. You can edit `logging.basicConfig` in `scraper/main.py`.
- Site Changes: If Prydwen.gg changes its HTML layout, you may need to update selectors or logic.

## Contributing 

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
