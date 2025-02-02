from invoke import task
import json
import sqlite3
from pathlib import Path


@task
def research(ctx, city="Seattle", num_bars=3):
    """Run cocktail bar research for a specific city"""
    # Wrap city in quotes to handle spaces
    ctx.run(f'python src/main.py --city "{city}" --num-bars {num_bars}')


@task
def show_usage(ctx):
    """Display usage statistics from the logs"""
    if Path("usage_logs.jsonl").exists():
        ctx.run("python src/core/tracking/show_usage.py")
    else:
        print("No usage logs found.")


@task
def clean_logs(ctx):
    """Clean up usage logs"""
    if Path("usage_logs.jsonl").exists():
        ctx.run("rm usage_logs.jsonl")
        print("Usage logs cleaned.")
    else:
        print("No usage logs to clean.")


@task
def setup(ctx):
    """Install the package in development mode"""
    ctx.run("uv pip install -e .")


@task
def show_bars(ctx, city=None):
    """Show all discovered bars for a city"""
    db_path = "data/bars.db"
    if not Path(db_path).exists():
        print("No database found. Run research first.")
        return

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if city:
            cursor = conn.execute("SELECT * FROM bars WHERE city = ?", (city,))
        else:
            cursor = conn.execute("SELECT city, COUNT(*) as count FROM bars GROUP BY city")
            results = cursor.fetchall()
            if not results:
                print("No bars found in database.")
                return
            print("\nBars found by city:")
            for row in results:
                print(f"{row['city']}: {row['count']} bars")
            return

        bars = cursor.fetchall()
        if not bars:
            print(f"No bars found for {city}")
            return

        print(f"\nFound {len(bars)} bars in {city}:")
        for bar in bars:
            print(f"\n{bar['name']}")
            if bar['website']:
                print(f"Website: {bar['website']}")
            if bar['description']:
                print(f"Description: {bar['description']}")


@task
def clean_db(ctx):
    """Remove the SQLite database to start fresh"""
    db_path = Path("data/bars.db")
    if db_path.exists():
        db_path.unlink()
        print("Database removed.")
    else:
        print("No database found.")


@task
def init(ctx):
    """Initialize project (install deps, create directories)"""
    # Create necessary directories
    Path("data").mkdir(exist_ok=True)

    # Install dependencies
    ctx.run("uv pip install -e .")

    # Check for config file
    if not Path("etc/config.toml").exists():
        print("\nWARNING: config.toml not found!")
        print("Please copy etc/config.template.toml to etc/config.toml")
        print("and add your API keys.")


@task
def find_menus(ctx, city=None, limit=None, force=False, verbose=False):
    """
    Find and screenshot cocktail menus for bars with websites

    Args:
        city: Optional city name to process
        limit: Maximum number of bars to process
        force: If True, reprocess bars even if they have menu data
        verbose: If True, show detailed progress
    """
    from components.menu_scraper.controller import MenuScraperController

    if verbose:
        print(f"Starting menu discovery for {'all cities' if city is None else city}")
        if limit:
            print(f"Processing up to {limit} bars")
        if force:
            print("Force mode: reprocessing all bars")

    scraper = MenuScraperController()

    # If force mode, clear existing menu data
    if force:
        with sqlite3.connect("data/bars.db") as conn:
            conn.execute("""
                UPDATE bars 
                SET menu_url = NULL,
                    raw_data = json_remove(raw_data, '$.menu_data')
                WHERE city = ? OR ? IS NULL
            """, (city, city))

    # Process bars
    scraper.process_bars_without_menus(
        city=city,
        limit=limit,
        verbose=verbose
    )