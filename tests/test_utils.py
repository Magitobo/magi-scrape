import pytest
import os
import json
from magiscrape.cli import sanitize_filename, extract_webpage_title

def test_sanitize_filename():
    assert sanitize_filename("hello world.html") == "hello_world.html"
    assert sanitize_filename("invalid/char:?.txt") == "char__.txt"
    assert sanitize_filename("../traversal") == "traversal"
    assert sanitize_filename("  spaces  ") == "spaces"
    assert sanitize_filename(None) == "unnamed_file"
    assert sanitize_filename("") == "unnamed_file"

def test_extract_webpage_title_fallback():
    # Test fallback when URL is unreachable or invalid
    title = extract_webpage_title("http://nonexistent.domain.example")
    assert "nonexistent_domain_example" in title

def test_extract_webpage_title_sanitization():
    # This is a bit harder to test without real network, but we can verify it handles
    # the case where the function is called with a malformed URL
    title = extract_webpage_title("invalid-url")
    assert "untitled_page" in title or "invalid-url" in title
