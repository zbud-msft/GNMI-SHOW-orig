"""Mock tests for show_cli to verify the wrapper script works."""

import subprocess
import tempfile
import os

import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOW_CLI = os.path.join(REPO_ROOT, "show_cli")


def run_show_cli(*args):
    """Run the local show_cli wrapper as a subprocess and return the result."""
    return subprocess.run(
        [SHOW_CLI, *args],
        capture_output=True,
        text=True,
    )


class TestCLIHelp:
    """Verify the CLI entry point is installed and responds correctly."""

    def test_help_flag(self):
        result = run_show_cli("--help")
        assert result.returncode == 0
        assert "show_cli" in result.stdout
        assert "--file" in result.stdout

    def test_help_contains_all_required_args(self):
        result = run_show_cli("--help")
        for flag in ["--file", "--switch_name", "--subscription_id",
                      "--resource_group", "--resource_name"]:
            assert flag in result.stdout, f"Missing required arg {flag} in help output"


class TestCLIArgValidation:
    """Verify the CLI rejects bad inputs before hitting any network calls."""

    def test_no_args_fails(self):
        result = run_show_cli()
        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_missing_file_arg_fails(self):
        result = run_show_cli(
            "-n", "switch1",
            "-s", "00000000-0000-0000-0000-000000000000",
            "-g", "rg-test",
            "-r", "res-test",
        )
        assert result.returncode != 0

    def test_nonexistent_file_fails(self):
        result = run_show_cli(
            "-f", "/tmp/does_not_exist_gnmi_test.txt",
            "-n", "switch1",
            "-s", "00000000-0000-0000-0000-000000000000",
            "-g", "rg-test",
            "-r", "res-test",
        )
        assert result.returncode == 2
        assert "not found" in result.stderr.lower() or "no such file" in result.stderr.lower()

    def test_empty_file_succeeds(self):
        """An empty command file should exit cleanly with no errors."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            tmp = f.name
        try:
            result = run_show_cli(
                "-f", tmp,
                "-n", "switch1",
                "-s", "00000000-0000-0000-0000-000000000000",
                "-g", "rg-test",
                "-r", "res-test",
            )
            assert result.returncode == 0
        finally:
            os.unlink(tmp)


class TestPathConverter:
    """Verify the sonic path converter module was bundled correctly."""

    def test_import_converter(self):
        from gnmi_show._sonic_path_converter import ShowCliToGnmiPathConverter
        assert ShowCliToGnmiPathConverter is not None

    def test_convert_known_path(self):
        from gnmi_show._sonic_path_converter import ShowCliToGnmiPathConverter
        converter = ShowCliToGnmiPathConverter(["show", "interfaces", "status"])
        path = converter.convert()
        assert path is not None
        assert len(path) > 0


class TestFormatter:
    """Verify the formatter wires through to the gnmi_cli_lib submodule."""

    def test_import_formatter(self):
        from gnmi_show.formatter import format_cli_output, formatter_version
        assert format_cli_output is not None
        assert formatter_version() != ""

    def test_format_known_command(self):
        from gnmi_show.formatter import format_cli_output
        output = format_cli_output(
            "show reboot-cause history",
            {"REBOOT_CAUSE|2026_03_12_16_04_36": {
                "cause": "reboot", "comment": "N/A",
                "time": "Thu Mar 12 04:00:12 PM UTC 2026", "user": "admin",
            }},
        )
        assert "reboot" in output
        assert "admin" in output


class TestWrapperScript:
    """Verify the bash wrapper itself."""

    def test_wrapper_exists_and_executable(self):
        assert os.path.isfile(SHOW_CLI), f"{SHOW_CLI} not found"
        assert os.access(SHOW_CLI, os.X_OK), f"{SHOW_CLI} is not executable"

    def test_wrapper_resolves_through_symlink(self, tmp_path):
        link = tmp_path / "show_cli_link"
        os.symlink(SHOW_CLI, link)
        result = subprocess.run([str(link), "--help"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "show_cli" in result.stdout
