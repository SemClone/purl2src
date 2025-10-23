"""Tests for CLI module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from purl2src.cli import main
from purl2src.handlers.base import HandlerResult


class TestCLI:
    """Test CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

        # Create a sample success result
        self.success_result = HandlerResult(
            purl="pkg:npm/express@4.17.1",
            download_url="https://registry.npmjs.org/express/-/express-4.17.1.tgz",
            validated=True,
            method="direct",
            fallback_command="npm view express@4.17.1 dist.tarball",
            status="success",
        )

        # Create a sample failed result
        self.failed_result = HandlerResult(
            purl="pkg:npm/nonexistent@1.0.0",
            download_url=None,
            validated=False,
            method="none",
            error="Failed to resolve download URL",
            status="failed",
        )

    def test_version_option(self):
        """Test --version option."""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_help_option(self):
        """Test --help option."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Translate Package URLs" in result.output
        assert "Examples:" in result.output

    @patch("purl2src.cli.get_download_url")
    def test_single_purl_success_plain_format(self, mock_get_url):
        """Test processing single PURL with plain output format."""
        mock_get_url.return_value = self.success_result

        result = self.runner.invoke(main, ["pkg:npm/express@4.17.1", "--format", "plain"])

        assert result.exit_code == 0
        assert (
            "pkg:npm/express@4.17.1 -> https://registry.npmjs.org/express/-/express-4.17.1.tgz"
            in result.output
        )
        mock_get_url.assert_called_once_with("pkg:npm/express@4.17.1", validate=True)

    @patch("purl2src.cli.get_download_url")
    def test_single_purl_success_json_format(self, mock_get_url):
        """Test processing single PURL with JSON output format."""
        mock_get_url.return_value = self.success_result

        result = self.runner.invoke(main, ["pkg:npm/express@4.17.1", "--format", "json"])

        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert len(output_json) == 1
        assert output_json[0]["purl"] == "pkg:npm/express@4.17.1"
        assert (
            output_json[0]["download_url"]
            == "https://registry.npmjs.org/express/-/express-4.17.1.tgz"
        )
        assert output_json[0]["status"] == "success"

    @patch("purl2src.cli.get_download_url")
    def test_single_purl_success_csv_format(self, mock_get_url):
        """Test processing single PURL with CSV output format."""
        mock_get_url.return_value = self.success_result

        result = self.runner.invoke(main, ["pkg:npm/express@4.17.1", "--format", "csv"])

        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert len(lines) == 2
        assert lines[0] == "purl,download_url,status,method"
        assert (
            "pkg:npm/express@4.17.1,https://registry.npmjs.org/express/-/express-4.17.1.tgz,success,direct"
            in lines[1]
        )

    @patch("purl2src.cli.get_download_url")
    def test_single_purl_failure(self, mock_get_url):
        """Test processing single PURL that fails."""
        mock_get_url.return_value = self.failed_result

        result = self.runner.invoke(main, ["pkg:npm/nonexistent@1.0.0"])

        assert result.exit_code == 1
        assert "pkg:npm/nonexistent@1.0.0 -> ERROR: Failed to resolve download URL" in result.output

    @patch("purl2src.cli.get_download_url")
    def test_validation_flag_disabled(self, mock_get_url):
        """Test --no-validate flag."""
        mock_get_url.return_value = self.success_result

        result = self.runner.invoke(main, ["pkg:npm/express@4.17.1", "--no-validate"])

        assert result.exit_code == 0
        mock_get_url.assert_called_once_with("pkg:npm/express@4.17.1", validate=False)

    @patch("purl2src.cli.get_download_url")
    def test_validation_flag_enabled(self, mock_get_url):
        """Test --validate flag (default)."""
        mock_get_url.return_value = self.success_result

        result = self.runner.invoke(main, ["pkg:npm/express@4.17.1", "--validate"])

        assert result.exit_code == 0
        mock_get_url.assert_called_once_with("pkg:npm/express@4.17.1", validate=True)

    @patch("purl2src.cli.get_download_url")
    def test_batch_processing_from_file(self, mock_get_url):
        """Test batch processing from file."""

        # Setup mock to return different results for different PURLs
        def mock_side_effect(purl, validate=True):
            if "express" in purl:
                return self.success_result
            else:
                return self.failed_result

        mock_get_url.side_effect = mock_side_effect

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("pkg:npm/express@4.17.1\n")
            f.write("# This is a comment\n")
            f.write("pkg:npm/nonexistent@1.0.0\n")
            f.write("\n")  # Empty line
            temp_file = f.name

        try:
            result = self.runner.invoke(main, ["--file", temp_file, "--format", "json"])

            assert result.exit_code == 1  # Should exit with error due to one failure
            output_json = json.loads(result.output)
            assert len(output_json) == 2  # Should process 2 PURLs (ignore comment and empty line)

            # Check that both PURLs were processed
            purls_processed = [item["purl"] for item in output_json]
            assert "pkg:npm/express@4.17.1" in purls_processed
            assert "pkg:npm/nonexistent@1.0.0" in purls_processed

        finally:
            Path(temp_file).unlink()

    @patch("purl2src.cli.get_download_url")
    def test_output_to_file(self, mock_get_url):
        """Test writing output to file."""
        mock_get_url.return_value = self.success_result

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            result = self.runner.invoke(
                main,
                [
                    "pkg:npm/express@4.17.1",
                    "--output",
                    output_file,
                    "--format",
                    "json",
                    "--verbose",
                ],
            )

            assert result.exit_code == 0
            assert f"Results written to {output_file}" in result.output

            # Check file contents
            with open(output_file, "r") as f:
                content = json.load(f)
            assert len(content) == 1
            assert content[0]["purl"] == "pkg:npm/express@4.17.1"

        finally:
            Path(output_file).unlink()

    @patch("purl2src.cli.get_download_url")
    def test_verbose_mode_with_multiple_purls(self, mock_get_url):
        """Test verbose mode with multiple PURLs shows progress."""
        mock_get_url.return_value = self.success_result

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("pkg:npm/express@4.17.1\n")
            f.write("pkg:npm/lodash@4.17.21\n")
            f.write("pkg:npm/react@17.0.2\n")
            temp_file = f.name

        try:
            # Mock the progress bar to avoid Click's context manager requirement in tests
            with patch("click.progressbar") as mock_progressbar:
                mock_progressbar.return_value = [
                    "pkg:npm/express@4.17.1",
                    "pkg:npm/lodash@4.17.21",
                    "pkg:npm/react@17.0.2",
                ]

                result = self.runner.invoke(main, ["--file", temp_file, "--verbose"])

                assert result.exit_code == 0
                # Should have called progressbar with verbose mode
                mock_progressbar.assert_called_once()

        finally:
            Path(temp_file).unlink()

    @patch("purl2src.cli.get_download_url")
    def test_verbose_mode_with_errors(self, mock_get_url):
        """Test verbose mode shows error count."""
        mock_get_url.return_value = self.failed_result

        result = self.runner.invoke(main, ["pkg:npm/nonexistent@1.0.0", "--verbose"])

        assert result.exit_code == 1
        assert "Completed with 1 error(s)" in result.output

    @patch("purl2src.cli.get_download_url")
    def test_exception_handling(self, mock_get_url):
        """Test handling of exceptions during processing."""
        mock_get_url.side_effect = ValueError("Test error")

        result = self.runner.invoke(main, ["pkg:npm/express@4.17.1", "--format", "json"])

        assert result.exit_code == 1
        output_json = json.loads(result.output)
        assert len(output_json) == 1
        assert output_json[0]["purl"] == "pkg:npm/express@4.17.1"
        assert output_json[0]["download_url"] is None
        assert output_json[0]["status"] == "failed"
        assert output_json[0]["error"] == "Test error"

    def test_no_purls_provided(self):
        """Test error when no PURLs are provided."""
        result = self.runner.invoke(main, [])

        assert result.exit_code == 1
        assert "No PURLs provided" in result.output

    def test_invalid_file_path(self):
        """Test error with invalid file path."""
        result = self.runner.invoke(main, ["--file", "/nonexistent/file.txt"])

        # Click should handle this with its path validation
        assert result.exit_code != 0

    @patch("purl2src.cli.get_download_url")
    def test_mixed_success_and_failure(self, mock_get_url):
        """Test processing with mixed success and failure results."""
        results = [self.success_result, self.failed_result]
        mock_get_url.side_effect = results

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("pkg:npm/express@4.17.1\n")
            f.write("pkg:npm/nonexistent@1.0.0\n")
            temp_file = f.name

        try:
            # Mock progress bar for verbose mode
            with patch("click.progressbar") as mock_progressbar:
                mock_progressbar.return_value = [
                    "pkg:npm/express@4.17.1",
                    "pkg:npm/nonexistent@1.0.0",
                ]

                result = self.runner.invoke(
                    main, ["--file", temp_file, "--format", "plain", "--verbose"]
                )

                assert result.exit_code == 1  # Should exit with error
                assert (
                    "pkg:npm/express@4.17.1 -> https://registry.npmjs.org/express/-/express-4.17.1.tgz"
                    in result.output
                )
                assert (
                    "pkg:npm/nonexistent@1.0.0 -> ERROR: Failed to resolve download URL"
                    in result.output
                )
                assert "Completed with 1 error(s)" in result.output

        finally:
            Path(temp_file).unlink()

    @patch("purl2src.cli.get_download_url")
    def test_csv_output_with_missing_fields(self, mock_get_url):
        """Test CSV output handles missing fields gracefully."""
        # Create result with some missing fields
        partial_result = HandlerResult(
            purl="pkg:npm/test@1.0.0",
            download_url="https://example.com/test.tgz",
            validated=True,
            method="api",
            status="success",
            # fallback_command is None
        )
        mock_get_url.return_value = partial_result

        result = self.runner.invoke(main, ["pkg:npm/test@1.0.0", "--format", "csv"])

        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert len(lines) == 2
        assert "pkg:npm/test@1.0.0,https://example.com/test.tgz,success,api" in lines[1]

    @patch("purl2src.cli.get_download_url")
    def test_plain_output_with_no_url(self, mock_get_url):
        """Test plain output format when download URL is None."""
        mock_get_url.return_value = self.failed_result

        result = self.runner.invoke(main, ["pkg:npm/nonexistent@1.0.0", "--format", "plain"])

        assert result.exit_code == 1
        assert "pkg:npm/nonexistent@1.0.0 -> ERROR: Failed to resolve download URL" in result.output

    @patch("purl2src.cli.get_download_url")
    def test_file_with_comments_and_empty_lines(self, mock_get_url):
        """Test file processing ignores comments and empty lines."""

        # Return different results for different PURLs
        def mock_side_effect(purl, validate=True):
            if "express" in purl:
                return HandlerResult(
                    purl=purl,
                    download_url="https://registry.npmjs.org/express/-/express-4.17.1.tgz",
                    validated=validate,
                    method="direct",
                    status="success",
                )
            elif "lodash" in purl:
                return HandlerResult(
                    purl=purl,
                    download_url="https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
                    validated=validate,
                    method="direct",
                    status="success",
                )
            else:
                return self.success_result

        mock_get_url.side_effect = mock_side_effect

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("  \n")  # Line with only spaces
            f.write("pkg:npm/express@4.17.1\n")
            f.write("# Another comment\n")
            f.write("pkg:npm/lodash@4.17.21\n")
            f.write("\n")
            temp_file = f.name

        try:
            result = self.runner.invoke(main, ["--file", temp_file, "--format", "json"])

            assert result.exit_code == 0
            output_json = json.loads(result.output)
            assert len(output_json) == 2  # Should only process non-comment, non-empty lines
            purls = [item["purl"] for item in output_json]
            assert "pkg:npm/express@4.17.1" in purls
            assert "pkg:npm/lodash@4.17.21" in purls

        finally:
            Path(temp_file).unlink()
