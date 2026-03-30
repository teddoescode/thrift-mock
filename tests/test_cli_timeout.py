"""Unit tests for the --timeout CLI flag on the serve command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SIMPLE_THRIFT = FIXTURES_DIR / "simple_service.thrift"


def _invoke_serve(extra_args: list[str]):
    from thrift_mock.cli import serve

    runner = CliRunner()
    return runner.invoke(
        serve,
        ["--thrift", str(SIMPLE_THRIFT), "--port", "19999"] + extra_args,
        catch_exceptions=False,
    )


def test_serve_default_timeout_is_60():
    """When --timeout is omitted, create_mock_server receives timeout_seconds=60."""
    with patch("thrift_mock.cli.create_mock_server") as mock_create:
        mock_server = MagicMock()
        mock_server.serve.side_effect = SystemExit(0)
        mock_create.return_value = mock_server
        _invoke_serve([])

    _, kwargs = mock_create.call_args
    assert kwargs["timeout_seconds"] == 60


def test_serve_custom_timeout_is_passed_through():
    """--timeout 120 is forwarded as timeout_seconds=120 to create_mock_server."""
    with patch("thrift_mock.cli.create_mock_server") as mock_create:
        mock_server = MagicMock()
        mock_server.serve.side_effect = SystemExit(0)
        mock_create.return_value = mock_server
        _invoke_serve(["--timeout", "120"])

    _, kwargs = mock_create.call_args
    assert kwargs["timeout_seconds"] == 120
