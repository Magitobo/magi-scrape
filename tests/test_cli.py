import pytest
import sys
from magiscrape.cli import main

def test_cli_help(capsys):
    """Test that the CLI shows usage when no arguments are provided."""
    with pytest.raises(SystemExit) as excinfo:
        sys.argv = ["magiscrape"]
        main()
    
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Usage: magiscrape <config.json> <output_directory>" in captured.out

def test_cli_invalid_config(tmp_path, capsys):
    """Test that the CLI fails gracefully with a non-existent config file."""
    output_dir = tmp_path / "output"
    config_file = tmp_path / "missing.json"
    
    with pytest.raises(FileNotFoundError):
        sys.argv = ["magiscrape", str(config_file), str(output_dir)]
        main()
