# Crawl Module Changelog

## [2025-01-15] - Custom Folder Naming & Enhanced Testing
- **Added:** Optional "name" property to name start URLs
- **Enhanced:** Documentation with updated configuration examples
- **Added:** Comprehensive test suite with 14 new tests:
  - Custom name functionality tests
  - Title extraction tests with edge cases
  - SPA and Playwright integration tests
  - Spider functionality tests
- **Added:** Test fixtures and HTTP server infrastructure for robust testing
- **Improved:** Test organization with shared fixtures in `conftest.py`

## [2025-09-20] - Complete Crawler Rewrite
- **Replaced:** `legacy_crawler.py` with new `crawl_scrapy_playwright.py`
- **Enhanced:** Scrapy + Playwright integration for JavaScript-rendered content
- **Added:** Comprehensive documentation with usage examples
- **Improved:** Configuration-based crawling with JSON configs
- **Enhanced:** Error handling and logging with per-URL log files
- **Added:** Support for multiple concurrent URL crawling
- **Improved:** File naming conventions and conflict resolution

## [2025-09-19] - Enhanced Playwright Integration
- **Added**: Playwright-based web scraping for JavaScript-heavy pages (technical documentation sites)
- **Replaced**: Scrapy-splash approach with Playwright for better reliability
- **Improved**: JavaScript execution using real browser engines
- **Benefits**:
  - No Docker containers required
  - Faster setup and more reliable execution
  - Built-in support for modern web technologies
  - Lower resource usage

## [2025-01-04] - documentation platforms Crawling Strategy Expansion
- **Added**: Detailed analysis of three crawling approaches for vendor documentation
- **Documented**: Option A (documentation hub), Option B (Selenium rendering), Option C (Direct content crawling)
- **Identified**: Critical issues with Googlebot crawling - links return "OK" instead of content
- **Planned**: Context-aware crawling with breadcrumb hierarchy tracking
- **Listed**: Specific vendor resources for crawling (IDE documentation, Academy content, YouTube transcripts)
- **Analyzed**: Metadata reliability and context precision tradeoffs for RAG systems

## [2024-11-29] - Documentation and Strategy Research
- **Added**: Initial crawling strategy documentation for documentation platforms platform
- **Researched**: documentation platforms API endpoints and sitemap structure
- **Analyzed**: Context isolation strategies for different SDK versions and product lines
- **Documented**: Metadata extraction approaches (key-value vs text-based discovery)
- **Noted**: vendor repositories as alternative source with limitations

## [2024-09-25] - Initial Implementation
- **Added**: First crawler implementation with `legacy_crawler.py`
- **Implemented**: Basic Scrapy-based web scraping functionality
- **Established**: Foundation for documentation crawling system
