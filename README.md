# MagiScrape

MagiScrape is the fastest web-scraping engine for the Magitobo ecosystem. It is a highly configurable web crawler built on the Scrapy framework, enhanced with `scrapy-playwright` for JavaScript-heavy technical documentation.

## Key Features

- **JavaScript Rendering**: Uses Playwright to execute JavaScript, enabling the scraping of modern, dynamic web pages (like technical documentation sites) where static crawlers fail.
- **Configurable**: Driven by JSON configuration files specifying start URLs, allowed domains, depth limits, and regex-based allow/deny patterns.
- **RAG-Ready Output**: Downloads web pages and images, generating structured `.metadata.json` files for each resource to facilitate ingestion into Retrieval-Augmented Generation (RAG) pipelines.
- **Context Preservation**: Designed to maintain hierarchical context and metadata to ensure high-quality retrieval in RAG systems.
- **Efficiency**: Supports Scrapy's autothrottle and download delays to respect site limits while maximizing throughput.

## Installation

MagiScrape is best managed with [uv](https://github.com/astral-sh/uv).

```bash
# Clone the repository
git clone https://github.com/magitobo/magi-scrape.git
cd magi-scrape

# Install dependencies and create a virtual environment
uv pip install -e .

# Install Playwright browsers
uv run playwright install
# Ubuntu/Debian: May need additional dependencies
playwright install-deps
```

## Usage

Run the crawler using the `magiscrape` command:

```bash
magiscrape <config.json> <output_directory>
```

### Example

```bash
magiscrape examples/example_config_playwright.json ./output
```

## Configuration

The tool requires a JSON configuration file. See `examples/example_config_playwright.json` for a template:

```json
{
  "collection_name": "My Document Collection",
  "urls": [
    {
      "start_url": "https://example.com/docs/",
      "name": "Example Documentation",
      "allowed_domains": ["example.com"],
      "allow_patterns": ["/docs/.*"],
      "deny_patterns": ["admin"],
      "depth_limit": 2,
      "use_playwright": true
    }
  ],
  "global_settings": {
    "download_delay": 1,
    "autothrottle_enabled": true
  }
}
```

## License

MIT
