# Cocktail Research Project

A CrewAI-based system for researching cocktail bars and menus.

## Installation

```bash
# Clone the repository
git clone [your-repo-url]

# Set up the project (creates directories, installs dependencies)
invoke init

# Copy the config template and add your API keys
cp etc/config.template.toml etc/config.toml
```

## Usage

Research bars in a city:
```bash
# Basic usage (defaults to 3 bars)
invoke research --city="Seattle"

# Get more bars
invoke research --city="New York" --num-bars=5
```

View discovered bars:
```bash
# See all cities and their bar counts
invoke show-bars

# See details for a specific city
invoke show-bars --city="Seattle"
```

Manage data and logs:
```bash
# View API usage statistics
invoke show-usage

# Clean usage logs
invoke clean-logs

# Reset bar database (start fresh)
invoke clean-db
```

## Project Structure

```
src/
├── components/          # Main pipeline components
│   ├── bar_finder/     # Bar discovery functionality
│   ├── menu_scraper/   # Menu screenshot capture
│   └── menu_analyzer/  # OCR and analysis
├── core/               # Core infrastructure
│   ├── config/        # Configuration management
│   ├── tracking/      # Usage tracking
│   └── utils/         # Utility functions
├── models/            # Data structures
└── storage/          # Data persistence

data/                 # Local data storage
└── bars.db          # SQLite database of discovered bars
```

## Data Storage

The project uses SQLite to store discovered bars. The database is automatically created in `data/bars.db` and includes:
- Bar names and descriptions
- Websites and menu URLs
- Discovery timestamps
- Search queries used to find each bar

The database is gitignored and can be reset using `invoke clean-db`.

## TODO List

### Phase 1: Core Bar Finding & Cost Tracking
- [x] Fix price tracking for API queries
  - [x] Implement accurate token counting for CrewAI interactions
  - [x] Add detailed cost breakdown per API call
  - [x] Add running total cost display
- [x] Implement bar deduplication
  - [x] Design bar data model with unique identifiers
  - [x] Add logic to detect and merge duplicate entries
  - [x] Implement fuzzy matching for similar bar names
- [x] Add persistent storage for bars
  - [x] Design database schema
  - [x] Implement file I/O operations
  - [x] Add CRUD operations for bar data
- [ ] Add tests for core functionality
  - [ ] Unit tests for bar finder
  - [ ] Cost tracking tests
  - [ ] Storage tests

### Phase 2: Menu Collection
- [ ] Design menu URL extraction system
  - [ ] Add support for different website structures
  - [ ] Implement URL validation
  - [ ] Add rate limiting and retry logic
- [ ] Implement screenshot functionality
  - [ ] Research and select screenshot tool
  - [ ] Handle different viewport sizes
  - [ ] Add error handling for failed captures

### Phase 3: Menu Analysis
- [ ] Implement OCR pipeline
  - [ ] Select and integrate OCR library
  - [ ] Add pre-processing for better accuracy
  - [ ] Handle different menu formats
- [ ] Add cocktail information extraction
  - [ ] Design cocktail data model
  - [ ] Implement ingredient parsing
  - [ ] Add price extraction

### Infrastructure & Improvements
- [x] Add proper logging system
- [x] Implement configuration validation
- [ ] Add CI/CD pipeline
- [ ] Add development documentation
- [ ] Implement caching for API responses
- [ ] Add rate limiting for API calls

### Future Features
- [ ] Add menu change detection
- [ ] Implement price tracking over time
- [ ] Add support for cocktail recommendations
- [ ] Add support for bar ratings/reviews
- [ ] Implement user feedback system

## Configuration

1. Copy the template configuration file:
```bash
cp etc/config.template.toml etc/config.toml
```

2. Add your API keys to `etc/config.toml`:
```toml
[api]
brave_api_key = "your-brave-api-key"
openai_api_key = "your-openai-api-key"
```

⚠️ Never commit your actual `config.toml` file - it's ignored by git for security.