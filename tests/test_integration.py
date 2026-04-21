import pytest
import subprocess
import os
import json
from pathlib import Path

@pytest.mark.integration
def test_integration_simple(tmp_path):
    """Integration test for static site scraping."""
    config_path = Path(__file__).parent / "test_simple.json"
    output_dir = tmp_path / "output_simple"
    
    # Run magiscrape via subprocess to test the CLI entry point
    result = subprocess.run(
        ["magiscrape", str(config_path), str(output_dir)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    
    # Verify output structure
    # Path: output_simple/Test Simple Quotes/crawl_scrapy/Quotes_Static/
    target_dir = output_dir / "Test Simple Quotes" / "crawl_scrapy" / "Quotes_Static"
    assert target_dir.exists()
    
    # Check for index file and metadata
    html_files = list(target_dir.glob("*.html"))
    assert len(html_files) > 0
    
    metadata_files = list(target_dir.glob("*.metadata.json"))
    assert len(metadata_files) > 0
    
    # Verify metadata content
    with open(metadata_files[0], 'r') as f:
        metadata = json.load(f)
        assert "url" in metadata
        assert metadata["collection_name"] == "Test Simple Quotes"

@pytest.mark.integration
def test_integration_complex(tmp_path):
    """Integration test for JS-rendered site scraping using Playwright."""
    config_path = Path(__file__).parent / "test_complex.json"
    output_dir = tmp_path / "output_complex"
    
    # Ensure playwright is installed (usually done in CI/env setup)
    # We assume it's already installed as per previous steps
    
    result = subprocess.run(
        ["magiscrape", str(config_path), str(output_dir)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    
    target_dir = output_dir / "Test Complex Quotes" / "crawl_scrapy" / "Quotes_JS"
    assert target_dir.exists()
    
    # Verify JS rendering worked by checking for specific text that only appears after JS execution
    html_files = list(target_dir.glob("*_index.html"))
    assert len(html_files) > 0
    
    content = html_files[0].read_text(encoding='utf-8')
    # This specific quote is rendered via JS on http://quotes.toscrape.com/js/
    assert "The world as we have created it is a process of our thinking" in content
    assert "Albert Einstein" in content
