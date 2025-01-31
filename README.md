# Cocktail Research Project

A CrewAI-based system for researching cocktail bars and menus.

## Installation

```bash
# Clone the repository
git clone [your-repo-url]

# Install dependencies
invoke setup
```

## Usage

```bash
# Research cocktail bars in a city
invoke research --city "Seattle" --num-bars 3

# View usage statistics
invoke show-usage

# Clean usage logs
invoke clean-logs
```

## Project Structure

```
src/
├── components/          # Main pipeline components
│   ├── bar_finder/     # Bar discovery functionality
│   ├── menu_scraper/   # Menu screenshot capture
│   └── menu_analyzer/  # OCR and analysis
├── core/               # Core infrastructure
└── models/            # Data structures
```

## TODO List

### Phase 1: Core Bar Finding & Cost Tracking
- [ ] Fix price tracking for API queries
  - [ ] Implement accurate token counting for CrewAI interactions
  - [ ] Add detailed cost breakdown per API call
  - [ ] Add running total cost display
- [ ] Implement bar deduplication
  - [ ] Design bar data model with unique identifiers
  - [ ] Add logic to detect and merge duplicate entries
  - [ ] Implement fuzzy matching for similar bar names
- [ ] Add persistent storage for bars
  - [ ] Design database schema
  - [ ] Implement file I/O operations
  - [ ] Add CRUD operations for bar data
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
- [ ] Add proper logging system
- [ ] Implement configuration validation
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

# Configuration

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