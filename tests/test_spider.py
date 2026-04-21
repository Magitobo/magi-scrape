import pytest
from magiscrape.cli import SimpleSpider

def test_spider_initialization():
    """Test that the spider initializes correctly with patterns."""
    spider = SimpleSpider(
        start_url="http://example.com",
        allowed_domains=["example.com"],
        allow_patterns=[".*guide.*"],
        deny_patterns=[".*private.*"],
        depth_limit=3,
        use_playwright=True
    )
    
    assert spider.start_urls == ["http://example.com"]
    assert spider.allowed_domains == ["example.com"]
    assert spider.depth_limit == 3
    assert spider.use_playwright is True

def test_spider_link_extractor_setup():
    """Test that the LinkExtractor is set up with the correct patterns."""
    spider = SimpleSpider(
        allow_patterns=[".*guide.*"],
        deny_patterns=[".*private.*"]
    )
    
    # Check the rules created by CrawlSpider
    rule = spider.rules[0]
    # Check that patterns are compiled into the link extractor
    # Note: LinkExtractor compiles them into regex objects
    allow_res = [r.pattern for r in rule.link_extractor.allow_res]
    deny_res = [r.pattern for r in rule.link_extractor.deny_res]
    
    assert ".*guide.*" in allow_res
    assert ".*private.*" in deny_res
