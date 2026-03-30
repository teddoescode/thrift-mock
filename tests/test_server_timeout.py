"""Unit tests for create_mock_server timeout parameter."""

from unittest.mock import MagicMock, patch


def test_create_mock_server_passes_default_timeout_as_milliseconds():
    """Default 60 s → 60000 ms passed to make_server."""
    from thrift_mock.server import create_mock_server

    mock_module = MagicMock()
    mock_handler = MagicMock()

    with patch("thrift_mock.server.make_server") as mock_make_server:
        mock_make_server.return_value = MagicMock()
        create_mock_server(mock_module, "SomeService", mock_handler, port=9999)

    _, kwargs = mock_make_server.call_args
    assert kwargs["client_timeout"] == 60_000


def test_create_mock_server_converts_custom_timeout_to_milliseconds():
    """Custom 30 s → 30000 ms passed to make_server."""
    from thrift_mock.server import create_mock_server

    mock_module = MagicMock()
    mock_handler = MagicMock()

    with patch("thrift_mock.server.make_server") as mock_make_server:
        mock_make_server.return_value = MagicMock()
        create_mock_server(
            mock_module, "SomeService", mock_handler, port=9999, timeout_seconds=30
        )

    _, kwargs = mock_make_server.call_args
    assert kwargs["client_timeout"] == 30_000


def test_create_mock_server_accepts_zero_timeout():
    """Zero seconds → 0 ms (no timeout in thriftpy2)."""
    from thrift_mock.server import create_mock_server

    mock_module = MagicMock()
    mock_handler = MagicMock()

    with patch("thrift_mock.server.make_server") as mock_make_server:
        mock_make_server.return_value = MagicMock()
        create_mock_server(
            mock_module, "SomeService", mock_handler, port=9999, timeout_seconds=0
        )

    _, kwargs = mock_make_server.call_args
    assert kwargs["client_timeout"] == 0
