## Summary
This project is a configurable web crawler built on the Scrapy framework, enhanced with `scrapy-playwright` for JavaScript-heavy technical documentation. 
## Key Features
- **JavaScript Rendering**: Uses Playwright to execute JavaScript, enabling the scraping of modern, dynamic web pages where static crawlers fail.
- **Configurable**: Driven by JSON configuration files specifying start URLs, allowed domains, depth limits, and regex-based allow/deny patterns for URL filtering.
- **RAG-Ready Output**: Downloads web pages and images, generating structured `.metadata.json` files for each resource to facilitate ingestion into Retrieval-Augmented Generation pipelines.
- **Context Preservation**: Designed to maintain hierarchical context and metadata (e.g., SDK versions, product lines) to ensure high-quality retrieval in RAG systems.
- **Efficiency**: Supports Scrapy's autothrottle and download delays to respect site limits while maximizing throughput.
## Usage
Run the crawler using: `python crawl_scrapy_playwright.py <config.json> <output_directory>`.
