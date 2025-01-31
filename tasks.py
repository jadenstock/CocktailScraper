from invoke import task

@task
def research(ctx, city="Seattle", num_bars=3):
    """Run cocktail bar research for a specific city"""
    # Keep the old command as a backup during transition
    # ctx.run(f"python src/cocktail_research/crew_cocktail_scraper.py --city {city} --num-bars {num_bars}")
    ctx.run(f"python src/main.py --city {city} --num-bars {num_bars}")

@task
def research_old(ctx, city="Seattle", num_bars=3):
    """Run the original cocktail bar research (keeping as backup)"""
    ctx.run(f"python src/cocktail_research/crew_cocktail_scraper.py --city {city} --num-bars {num_bars}")

@task
def show_usage(ctx):
    """Display usage statistics from the logs"""
    ctx.run("python src/cocktail_research/show_usage.py")

@task
def clean_logs(ctx):
    """Clean up usage logs"""
    ctx.run("rm usage_logs.jsonl")

@task
def setup(ctx):
    """Install the package in development mode"""
    ctx.run("uv pip install -e .")