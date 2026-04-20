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
- **Replaced:** `crawl_scrapy_ccs_docs.py` with new `crawl_scrapy_playwright.py`
- **Enhanced:** Scrapy + Playwright integration for JavaScript-rendered content
- **Added:** Comprehensive documentation with usage examples
- **Improved:** Configuration-based crawling with JSON configs
- **Enhanced:** Error handling and logging with per-URL log files
- **Added:** Support for multiple concurrent URL crawling
- **Improved:** File naming conventions and conflict resolution

## [2025-09-19] - Enhanced Playwright Integration
- **Added**: Playwright-based web scraping for JavaScript-heavy pages (ARM documentation)
- **Replaced**: Scrapy-splash approach with Playwright for better reliability
- **Improved**: JavaScript execution using real browser engines
- **Benefits**:
  - No Docker containers required
  - Faster setup and more reliable execution
  - Built-in support for modern web technologies
  - Lower resource usage

## [2025-01-04] - TI Tirex Crawling Strategy Expansion
- **Added**: Detailed analysis of three crawling approaches for TI documentation
- **Documented**: Option A (Tirex sitemap), Option B (Selenium rendering), Option C (Direct content crawling)
- **Identified**: Critical issues with Googlebot crawling - links return "OK" instead of content
- **Planned**: Context-aware crawling with breadcrumb hierarchy tracking
- **Listed**: Specific TI resources for crawling (CCS User's Guide, Academy content, YouTube transcripts)
- **Analyzed**: Metadata reliability and context precision tradeoffs for RAG systems

## [2024-11-29] - Documentation and Strategy Research
- **Added**: Initial crawling strategy documentation for TI Tirex platform
- **Researched**: TI Tirex API endpoints and sitemap structure
- **Analyzed**: Context isolation strategies for different SDK versions and product lines
- **Documented**: Metadata extraction approaches (key-value vs text-based discovery)
- **Noted**: GitHub TI repositories as alternative source with limitations

## [2024-09-25] - Initial Implementation
- **Added**: First crawler implementation with `crawl_scrapy_ccs_docs.py`
- **Implemented**: Basic Scrapy-based web scraping functionality
- **Established**: Foundation for documentation crawling system
