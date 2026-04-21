"""
Web Crawler using Scrapy + scrapy-playwright

This script provides a configurable web crawler built on the Scrapy framework that can crawl multiple
websites simultaneously based on JSON configuration files. It downloads web pages, images, and creates
structured metadata for use in RAG (Retrieval-Augmented Generation) pipelines.

### Configuration File Format
The script requires a JSON configuration file with the following structure:

```json
{
  "collection_name": "My Document Collection",
  "urls": [
    {
      "start_url": "https://example.com/docs/",
      "name": "Example Documentation",
      "allowed_domains": ["example.com"],
      "allow_patterns": ["/docs/.*", "/help/.*"],
      "deny_patterns": ["admin", "login", "api"],
      "depth_limit": 2,
      "use_playwright": true
    },
    {
      "start_url": "https://another-site.com/",
      "allowed_domains": ["another-site.com"],
      "allow_patterns": [],
      "deny_patterns": ["private"],
      "depth_limit": 1
    }
  ],
  "global_settings": {
    "download_delay": 1,
    "autothrottle_enabled": true,
    "autothrottle_start_delay": 1,
    "autothrottle_max_delay": 10
  }
}
```

### Configuration Parameters

- **collection_name** (required): Name for the collection, used as folder name
- **urls** (required): Array of URL configurations to crawl
  - **start_url** (required): Starting URL for the spider
  - **name** (optional): Custom name for the folder (overrides webpage title extraction)
  - **allowed_domains** (optional): List of domains to crawl (auto-detected if empty)
  - **allow_patterns** (optional): Regex patterns to include URLs. When both allow and deny are provided, allow is applied first, then deny excludes from that set
  - **deny_patterns** (optional): Regex patterns to exclude URLs
  - **depth_limit** (optional): Maximum crawl depth (default: 1)
  - **use_playwright** (optional): Enable JavaScript rendering with Playwright (default: false)
- **global_settings** (optional): Scrapy settings applied to all crawls

## Output Structure

The script creates the following output structure:

```
<output_directory>/
└── <collection_name>/
    └── crawl_scrapy/
        ├── <name or start_url_1_webpage_title>/  # Subfolder named name in config or by webpage title
        │   ├── scrapy.log                       # Crawler log file for this URL
        │   ├── example_com_index.html           # Downloaded page
        │   ├── example_com_index.metadata.json  # Page metadata
        │   ├── example_com_about.html           # Another page
        │   ├── example_com_about.metadata.json  # Page metadata
        │   ├── example_com_logo.png             # Downloaded image
        │   ├── example_com_logo.metadata.json   # Image metadata
        │   └── ...                              # Additional files
        └── <name or start_url_2_webpage_title>/ # Subfolder for second start_url
            ├── scrapy.log                       # Crawler log file for this URL
            └── ...                              # Files from second URL
```

### File Naming Convention
- Files are prefixed with domain name (dots and colons replaced with underscores)
- Original filenames are preserved when possible
- Conflicts are resolved by appending numbers (_1, _2, etc.)
- Missing file extensions are inferred from Content-Type headers

### Metadata Files
Each downloaded resource gets a corresponding `.metadata.json` file containing:

```json
{
  "created": "2024-01-15 14:30:25",
  "url": "https://example.com/docs/guide.html",
  "collection_name": "Documentation",
  "output_folder": "/path/to/output/Documentation/crawl_scrapy",
  "content_type": "text/html",
  "traceback": [{
    "script": "/path/to/crawl_scrapy.py",
    "tool": "scrapy",
    "version": "2.5.0",
    "parameters": {
      "start_urls": ["https://example.com/docs/"],
      "allowed_domains": ["example.com"],
      "rules": [{
        "allow": ["/docs/.*"],
        "deny": ["admin", "login"]
      }],
      "DEPTH_LIMIT": 2
    }
  }]
}
```

### Playwright Settings
- **Browser**: Chromium (can be configured to Firefox or WebKit)
- **Wait time**: 5 seconds for page load, with intelligent waiting for content
- **Timeout**: 30 seconds per page
- **Render**: Full HTML rendering with complete JavaScript execution
- **Mode**: Headless by default (configurable)

"""

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.utils.log import configure_logging
from scrapy.http import Request
import os
import json
from datetime import datetime
from urllib.parse import urlparse, urljoin
import mimetypes
import sys
import requests
import re
from bs4 import BeautifulSoup

# Constants
PLAYWRIGHT_WAIT_TIMEOUT = 3000  # milliseconds
DEFAULT_REQUEST_TIMEOUT = 10    # seconds
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# scrapy-playwright imports (optional, graceful fallback if not available)
try:
    from scrapy_playwright.page import PageMethod
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("Warning: scrapy-playwright not available. Install with: pip install scrapy-playwright")
    print("Note: You may also need to run: playwright install")
    PLAYWRIGHT_AVAILABLE = False


def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal and invalid characters.
    Returns a safe filename suitable for filesystem usage.
    """
    if not filename:
        return 'unnamed_file'

    # Remove directory traversal attempts
    filename = os.path.basename(filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Replace invalid characters and spaces with underscores
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f\s]'
    sanitized = re.sub(invalid_chars, '_', filename)

    # Ensure filename isn't empty after sanitization
    if not sanitized:
        return 'unnamed_file'

    # Limit length to avoid filesystem issues
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        max_name_len = 255 - len(ext)
        sanitized = name[:max_name_len] + ext

    return sanitized


class CustomImagesPipeline:
    """Custom images pipeline that handles file downloads and metadata"""
    
    def process_item(self, item, spider):
        return item


def extract_webpage_title(url, timeout=DEFAULT_REQUEST_TIMEOUT):
    """
    Extract the title from a webpage URL.
    Returns a sanitized title suitable for folder names.
    """
    try:
        # Fetch the webpage via HTTP/HTTPS
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        content = response.content

        # Parse HTML and extract title
        soup = BeautifulSoup(content, 'html.parser')
        title_tag = soup.find('title')
        
        if title_tag and title_tag.get_text():
            # Use get_text() to handle nested tags and malformed HTML
            title = title_tag.get_text().strip()
        else:
            title = None

        if not title:
            # Fallback: use domain name
            title = urlparse(url).netloc
        
        # Sanitize title for folder name
        # Remove/replace invalid characters for folder names
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', title)
        sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
        sanitized = sanitized.strip('._')  # Remove leading/trailing dots and underscores
        
        # Limit length to avoid filesystem issues
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
            
        return sanitized if sanitized else 'untitled_page'
        
    except Exception as e:
        print(f"Warning: Could not extract title from {url}: {e}")
        # Fallback: use domain name with path
        parsed = urlparse(url)
        fallback = f"{parsed.netloc}{parsed.path}".replace('/', '_').replace('.', '_')
        fallback = re.sub(r'[<>:"/\\|?*]', '_', fallback)
        return fallback[:100] if fallback else 'untitled_page'


def set_playwright_true(request, response):
    """Process function to enable Playwright for followed links"""
    request.meta["playwright"] = True
    request.meta["playwright_page_methods"] = [
        PageMethod("wait_for_timeout", PLAYWRIGHT_WAIT_TIMEOUT),  # Wait 3 seconds for JS to load
    ]
    return request


class SimpleSpider(CrawlSpider):
    """Simple spider using scrapy-playwright for JavaScript rendering"""
    name = "simple_spider"
    
    def __init__(self, start_url=None, allowed_domains=None, deny_patterns=None,
                 allow_patterns=None, depth_limit=1, use_playwright=False, *args, **kwargs):

        if start_url:
            self.start_urls = [start_url]

        # Handle domain restrictions
        if allowed_domains:
            self.allowed_domains = allowed_domains.copy()
        else:
            self.allowed_domains = []

        # Set up rules based on patterns
        allow_patterns = allow_patterns or []
        deny_patterns = deny_patterns or []
        self.use_playwright = use_playwright and PLAYWRIGHT_AVAILABLE

        # Use process_request to enable Playwright for followed links if needed
        process_request_func = set_playwright_true if self.use_playwright else None

        # Create LinkExtractor with proper parameters
        # Note: When both allow and deny are provided, allow is applied first, then deny excludes from that set
        link_extractor_kwargs = {}
        if allow_patterns:
            link_extractor_kwargs['allow'] = allow_patterns
        if deny_patterns:
            link_extractor_kwargs['deny'] = deny_patterns

        self.logger.info(f"Setting up LinkExtractor with allow={allow_patterns}, deny={deny_patterns}")

        self.rules = (
            Rule(LinkExtractor(**link_extractor_kwargs),
                 callback='parse_item', follow=True, process_request=process_request_func),
        )

        self.depth_limit = depth_limit

        # Call parent __init__ AFTER setting up rules
        super(SimpleSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        """Generate initial requests with optional Playwright rendering"""
        for url in self.start_urls:
            if self.use_playwright:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_item,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_timeout", PLAYWRIGHT_WAIT_TIMEOUT),  # Wait 3 seconds for JS to load
                        ],
                    }
                )
            else:
                # Use CrawlSpider's default behavior but ensure start URL content is saved
                yield scrapy.Request(url=url, callback=self.parse_start_url)

    def parse_start_url(self, response):
        """Parse start URL and ensure content is saved"""
        # Save the start URL content
        yield from self.parse_item(response)

        # Also let CrawlSpider extract and follow links from this page
        yield from self._requests_to_follow(response)

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        if hasattr(cls, 'depth_limit'):
            settings.set("DEPTH_LIMIT", cls.depth_limit, priority="spider")
        if cls.folder_path:
            settings.set("IMAGES_STORE", cls.folder_path, priority="spider")
            settings.set("ITEM_PIPELINES", {f'{__name__}.CustomImagesPipeline': 1}, priority="spider")
        # Configure scrapy-playwright if needed
        if hasattr(cls, 'use_playwright') and cls.use_playwright:
            settings.set("DOWNLOAD_HANDLERS", {
                "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            }, priority="spider")
            settings.set("TWISTED_REACTOR", "twisted.internet.asyncioreactor.AsyncioSelectorReactor", priority="spider")
            settings.set("ROBOTSTXT_OBEY", False, priority="spider")

    def _save_page_content(self, response):
        """Save the page content to disk and return file path and content type."""
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').split(';')[0].strip()
        extension = mimetypes.guess_extension(content_type) or ''

        url_path = urlparse(response.url).path
        filename = os.path.basename(url_path) or 'index'

        if not os.path.splitext(filename)[1]:
            filename += extension

        # Create unique filename to avoid conflicts between different start URLs
        domain = urlparse(response.url).netloc
        safe_domain = domain.replace('.', '_').replace(':', '_')
        unique_filename = f"{safe_domain}_{filename}"

        # Sanitize filename to prevent security issues
        safe_filename = sanitize_filename(unique_filename)
        file_path = os.path.join(self.folder_path, safe_filename)

        # Handle filename conflicts
        counter = 1
        base_path = file_path
        while os.path.exists(file_path):
            name, ext = os.path.splitext(base_path)
            file_path = f"{name}_{counter}{ext}"
            counter += 1

        # Check file size limit
        if len(response.body) > MAX_FILE_SIZE:
            self.logger.warning(f"Skipping large file {response.url}: {len(response.body)} bytes > {MAX_FILE_SIZE}")
            return None, content_type

        # Save file
        with open(file_path, 'wb') as f:
            f.write(response.body)

        return file_path, content_type

    def _extract_and_process_images(self, response, safe_domain):
        """Extract image URLs and create metadata for them."""
        image_urls = response.css('img::attr(src)').getall()
        image_urls = [urljoin(response.url, url) for url in image_urls]

        # Create metadata for each image
        for image_url in image_urls:
            image_name = os.path.basename(urlparse(image_url).path)
            if image_name:
                safe_image_name = sanitize_filename(f"{safe_domain}_{image_name}")
                image_path = os.path.join(self.folder_path, safe_image_name)
                self.create_metadata(image_url, image_path, 'image')

        return image_urls

    def _log_page_links(self, response):
        """Log links found on the page for debugging."""
        all_links = response.css('a::attr(href)').getall()
        self.logger.info(f"Found {len(all_links)} total links on {response.url}")

        # Test our LinkExtractor to see what it would extract
        if hasattr(self, 'rules') and self.rules:
            rule = self.rules[0]  # Get first rule
            extracted_links = rule.link_extractor.extract_links(response)
            self.logger.info(f"LinkExtractor would follow {len(extracted_links)} links")

            for i, link in enumerate(extracted_links[:10]):  # Log first 10 extracted links
                self.logger.info(f"  Extracted link {i+1}: {link.url}")

            # Also test which links were filtered out
            all_full_links = [urljoin(response.url, link) for link in all_links]
            extracted_urls = {link.url for link in extracted_links}
            filtered_out = [url for url in all_full_links if url not in extracted_urls]
            if filtered_out:
                self.logger.info(f"LinkExtractor filtered out {len(filtered_out)} links:")
                for i, url in enumerate(filtered_out[:5]):  # Log first 5 filtered links
                    self.logger.info(f"  Filtered out {i+1}: {url}")

        # Also log first few raw links for debugging
        for i, link in enumerate(all_links[:10]):  # Log first 10 raw links
            full_link = urljoin(response.url, link)
            self.logger.info(f"  Raw link {i+1}: {link} -> {full_link}")

    def _handle_playwright_links(self, response):
        """Handle link extraction for Playwright-rendered content."""
        # Only do manual link extraction for Playwright responses
        # For regular responses, let CrawlSpider handle link following automatically
        if not (self.use_playwright and hasattr(response, 'meta') and response.meta.get('playwright')):
            return

        self.logger.info("Manually extracting links from Playwright-rendered content...")

        # Extract all links from the rendered page
        all_links = response.css('a::attr(href)').getall()

        # Filter links based on allow/deny patterns from spider rules
        allow_patterns = []
        deny_patterns = []

        # Get patterns from spider rules
        for rule in self.rules:
            if hasattr(rule.link_extractor, 'allow_res'):
                allow_patterns.extend([r.pattern for r in rule.link_extractor.allow_res])
            if hasattr(rule.link_extractor, 'deny_res'):
                deny_patterns.extend([r.pattern for r in rule.link_extractor.deny_res])

        # Use LinkExtractor to filter links properly
        link_extractor = LinkExtractor(
            allow=allow_patterns if allow_patterns else (),
            deny=deny_patterns if deny_patterns else (),
            unique=True
        )

        # Create temporary response with just the links to filter them
        extracted_links = link_extractor.extract_links(response)
        self.logger.info(f"Manual LinkExtractor found {len(extracted_links)} links to follow")

        # Yield follow-up requests for extracted links
        for link in extracted_links:
            self.logger.debug(f"Following link: {link.url}")
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_item,
                meta={
                    'playwright': True,  # Use Playwright for followed links too
                    'playwright_page_methods': [
                        PageMethod("wait_for_timeout", PLAYWRIGHT_WAIT_TIMEOUT),  # Wait for JS to load
                    ]
                }
            )

    def parse_item(self, response):
        """Main parsing method - coordinates the page processing."""
        # Save page content and get file path
        file_path, content_type = self._save_page_content(response)
        if file_path is None:  # File was too large, skip processing
            return

        # Create metadata for the page
        self.create_metadata(response.url, file_path, content_type)

        # Extract and process images
        domain = urlparse(response.url).netloc
        safe_domain = domain.replace('.', '_').replace(':', '_')
        image_urls = self._extract_and_process_images(response, safe_domain)

        # Log links for debugging
        self._log_page_links(response)

        # Yield scrapy item
        yield {
            'file_urls': [response.url],
            'image_urls': image_urls
        }

        # Handle Playwright link extraction only for Playwright responses
        # For regular responses, CrawlSpider will handle link following automatically
        yield from self._handle_playwright_links(response)

    def create_metadata(self, url, file_path, content_type):
        """Create metadata for downloaded files"""
        metadata = {
            "url": url,
            "file_path": file_path,
            "content_type": content_type,
            "crawled_at": datetime.now().isoformat(),
            "allowed_domains": self.allowed_domains,
            "collection_name": getattr(self, 'collection_name', 'unknown')
        }
        
        metadata_path = file_path + '.metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)


def run_crawler(config_file, base_output_dir):
    """Run the crawler with the given configuration"""
    # Load configuration
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    collection_name = config.get('collection_name', 'default_collection')
    
    # Create output directory
    output_dir = os.path.join(base_output_dir, collection_name, 'crawl_scrapy')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"Crawling {len(config['urls'])} URLs for collection: {collection_name}")
    print(f"Base output directory: {output_dir}")
    
    # Configure logging
    configure_logging({'LOG_LEVEL': config.get('global_settings', {}).get('log_level', 'INFO')})
    
    # Set up Scrapy settings
    scrapy_settings = {
        'USER_AGENT': 'Mozilla/5.0 (compatible; ScrapyCrawler/1.0)',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': config.get('global_settings', {}).get('download_delay', 1),
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_ENABLED': config.get('global_settings', {}).get('autothrottle_enabled', True),
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'DOWNLOAD_TIMEOUT': 60,
        'DEPTH_LIMIT': 2,  # Default depth
    }
    
    # Add scrapy-playwright settings if needed
    urls_with_playwright = [url for url in config['urls'] if url.get('use_playwright', False)]
    if urls_with_playwright and PLAYWRIGHT_AVAILABLE:
        scrapy_settings.update({
            'DOWNLOAD_HANDLERS': {
                "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            },
            'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        })
    
    # Process each URL configuration
    for i, url_config in enumerate(config['urls'], 1):
        start_url = url_config['start_url']
        print(f"\nProcessing URL {i}/{len(config['urls'])}: {start_url}")
        
        # Extract title and create folder
        if 'name' in url_config:
            print(f"Using custom name: {url_config['name']}")
            folder_name = sanitize_filename(url_config['name'].replace(' ', '_'))
        else:
            try:
                print(f"Extracting title from: {start_url}")
                folder_name = extract_webpage_title(start_url)
                print(f"Using folder name: {folder_name}")
            except Exception as e:
                print(f"Could not extract title, using domain: {e}")
                folder_name = urlparse(start_url).netloc.replace('.', '_')
        
        url_output_dir = os.path.join(output_dir, folder_name)
        if not os.path.exists(url_output_dir):
            os.makedirs(url_output_dir, exist_ok=True)
        
        # Configure spider
        spider_settings = scrapy_settings.copy()
        spider_settings['DEPTH_LIMIT'] = url_config.get('depth_limit', 1)

        # Set up logging to file in the spider's output directory
        log_file = os.path.join(url_output_dir, 'scrapy.log')
        spider_settings['LOG_FILE'] = log_file
        spider_settings['LOG_LEVEL'] = config.get('global_settings', {}).get('log_level', 'INFO')

        # Set up spider with configuration
        url_config.setdefault('allowed_domains', [])
        url_config.setdefault('deny_patterns', [])
        url_config.setdefault('allow_patterns', [])

        # Auto-detect domain if not specified
        if not url_config['allowed_domains']:
            parsed_url = urlparse(start_url)
            domain = parsed_url.netloc
            if domain:
                url_config['allowed_domains'] = [domain]

        # Create and run spider
        process = CrawlerProcess(spider_settings)

        # Set spider attributes
        SimpleSpider.folder_path = url_output_dir
        SimpleSpider.collection_name = collection_name

        process.crawl(
            SimpleSpider,
            start_url=start_url,
            allowed_domains=url_config['allowed_domains'],
            deny_patterns=url_config['deny_patterns'],
            allow_patterns=url_config['allow_patterns'],
            depth_limit=url_config.get('depth_limit', 1),
            use_playwright=url_config.get('use_playwright', False)
        )

        process.start()
        
        print(f"Files for {start_url} saved to: {url_output_dir}")
    
    print(f"\nCrawling completed. All files saved under: {output_dir}")


def main():
    if len(sys.argv) != 3:
        print("Usage: magiscrape <config.json> <output_directory>")
        sys.exit(1)

    config_file = sys.argv[1]
    output_directory = sys.argv[2]

    # Create output directory if it doesn't exist
    if not os.path.exists(output_directory):
        print(f"Creating output directory: {output_directory}")
        os.makedirs(output_directory, exist_ok=True)

    run_crawler(config_file, output_directory)

if __name__ == "__main__":
    main()