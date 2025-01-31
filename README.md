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

### High Priority
- [ ] Add tests for bar_finder component
- [ ] Implement menu URL extraction
- [ ] Add proper error handling for API failures
- [ ] Add caching for API responses
- [ ] Add rate limiting for API calls

### Menu Scraping Component
- [ ] Design menu scraping architecture
- [ ] Implement screenshot capture functionality
- [ ] Add URL validation and sanitization
- [ ] Handle different menu formats (PDF, images, HTML)

### OCR Component
- [ ] Research and select OCR library
- [ ] Implement basic OCR functionality
- [ ] Add menu text extraction
- [ ] Design cocktail information parser

### Infrastructure
- [ ] Add proper logging system
- [ ] Implement data persistence layer
- [ ] Add configuration validation
- [ ] Add CI/CD pipeline
- [ ] Add documentation for all components

### Features
- [ ] Add support for more search parameters
- [ ] Implement cocktail menu versioning
- [ ] Add support for price tracking
- [ ] Add support for menu change detection

### Documentation
- [ ] Add API documentation
- [ ] Add development setup guide
- [ ] Add contribution guidelines
- [ ] Document architecture decisions