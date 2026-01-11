"""CLI integration tests"""

import pytest
from click.testing import CliRunner

from javinizer.cli import main


@pytest.fixture
def runner():
    """Create CLI test runner"""
    return CliRunner()


class TestCLI:
    """Test CLI commands"""

    def test_main_help(self, runner):
        """Test main help displays correctly"""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Javinizer" in result.output

    def test_version(self, runner):
        """Test version option"""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_find_help(self, runner):
        """Test find command help"""
        result = runner.invoke(main, ["find", "--help"])
        assert result.exit_code == 0
        assert "movie_id" in result.output.lower() or "MOVIE_ID" in result.output

    def test_sort_help(self, runner):
        """Test sort command help"""
        result = runner.invoke(main, ["sort", "--help"])
        assert result.exit_code == 0

    def test_config_help(self, runner):
        """Test config command help"""
        result = runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0

    def test_config_show(self, runner):
        """Test config show command runs without error"""
        result = runner.invoke(main, ["config", "show"])
        # Should not crash, may have exit code 0 or show config
        assert result.exit_code == 0 or "Configuration" in result.output or "Config" in result.output

    def test_thumbs_help(self, runner):
        """Test thumbs command help"""
        result = runner.invoke(main, ["thumbs", "--help"])
        assert result.exit_code == 0

    def test_update_help(self, runner):
        """Test update command help"""
        result = runner.invoke(main, ["update", "--help"])
        assert result.exit_code == 0

    def test_info_help(self, runner):
        """Test info command help"""
        result = runner.invoke(main, ["info", "--help"])
        assert result.exit_code == 0


class TestFindCommand:
    """Test find command specifically"""

    def test_find_missing_id_shows_error(self, runner):
        """Test that find without ID shows error"""
        result = runner.invoke(main, ["find"])
        # Should fail because MOVIE_ID is required
        assert result.exit_code != 0 or "Missing argument" in result.output or "Usage" in result.output


class TestConfigCommand:
    """Test config commands"""

    def test_set_proxy_no_args_shows_help(self, runner):
        """Test set-proxy without args shows help message"""
        result = runner.invoke(main, ["config", "set-proxy"])
        # Should prompt user or show current state
        assert result.exit_code == 0 or "Please provide" in result.output
